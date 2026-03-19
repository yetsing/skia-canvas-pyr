import json
import math
import os
from typing import Any, Callable, Dict, TypedDict, List

from . import css
from .canvas import Canvas
from .context import CanvasRenderingContext2D
from .event_emitter import EventEmitter

try:
    from ..skia_canvas_pyr import (
        register,
        open_window,
        close_window,
        activate,
        quit,
        set_mode,
        set_rate,
        wait_for_termination,
    )

    has_app_api = True
except ImportError:
    has_app_api = False


def _check_support():
    if not has_app_api:
        raise RuntimeError("Skia Canvas was compiled without window support")


def _handle_ui_event(win: "Window", type: str, e: Dict[str, Any]):
    match type:
        case "mouse":
            # 直接取值（若字段必须存在，用 e['button'] 等）；下面用 .get 并在可能为 None 时用空 dict 作为后备
            button = e.get("button")
            buttons = e.get("buttons")
            point = e.get("point") or {}  # 避免 None 导致 **point 抛错
            page_point = e.get("page_point") or {}
            pageX = page_point.get("x")
            pageY = page_point.get("y")
            modifiers = e.get("modifiers") or {}  # 避免 None 导致 **modifiers 抛错

            payload = {
                "button": button,
                "buttons": buttons,
                **point,  # 展开 point 的键
                "pageX": pageX,  # 覆盖来自 point 的同名键（如果有的话）
                "pageY": pageY,
                **modifiers,  # modifiers 的键会覆盖之前同名的键
            }

            win.emit(e["event"], payload)

        case "input":
            data = e.get("data")
            inputType = e.get("inputType")
            win.emit(type, {"data": data, "inputType": inputType})

        case "composition":
            win.emit(e["event"], {"data": e.get("data"), "locale": _App._locale})

        case "keyboard":
            event = e["event"]
            key = e.get("key")
            code = e.get("code")
            location = e.get("location")
            repeat = bool(e.get("repeat"))  # ensure boolean
            modifiers = e.get("modifiers") or {}  # ensure mapping; avoid **None

            # defaults flag controlled by prevent_default callback
            defaults = True

            def preventDefault():
                nonlocal defaults
                defaults = False

            win.emit(
                event,
                {
                    "key": key,
                    "code": code,
                    "location": location,
                    "repeat": repeat,
                    **modifiers,
                    "preventDefault": preventDefault,
                },
            )

            # apply default keybindings unless e.preventDefault() was run
            if defaults and event == "keydown" and not repeat:
                ctrlKey = modifiers.get("ctrlKey")
                altKey = modifiers.get("altKey")
                metaKey = modifiers.get("metaKey")
                if (
                    (metaKey and key == "w")
                    or (ctrlKey and key == "c")
                    or (altKey and key == "F4")
                ):
                    win.close()
                elif (metaKey and key == "f") or (altKey and key == "F8"):
                    win.fullscreen = not win.fullscreen

        case "focus":
            if e:
                win.emit("focus")
            else:
                win.emit("blur")

        case "resize":
            if win.fit == "resize":
                win.ctx.raw_set_size(e["width"], e["height"])
                win.canvas.raw_set_width(e["width"])
                win.canvas.raw_set_height(e["height"])
            win.emit(type, e)

        case "move" | "wheel":
            win.emit(type, e)

        case "fullscreen":
            win.emit(type, {"enabled": e})

        case _:
            print(type, e)


class WindowEvent:
    open = "open"
    idle = "idle"

    mousedown = "mousedown"
    mouseup = "mouseup"
    mousemove = "mousemove"
    wheel = "wheel"

    keydown = "keydown"
    keyup = "keyup"
    input = "input"
    compositionstart = "compositionstart"
    compositionupdate = "compositionupdate"
    compositionend = "compositionend"

    close = "close"
    fullscreen = "fullscreen"
    move = "move"
    resize = "resize"

    setup = "setup"
    frame = "frame"
    draw = "draw"

    blur = "blur"
    focus = "focus"


class _App(EventEmitter):
    __slots__ = (
        "_event_loop_mode",
        "_started",
        "_launcher",
        "_windows",
        "_frames",
        "_fps",
    )

    _locale = (
        os.environ.get("LC_ALL")
        or os.environ.get("LC_MESSAGES")
        or os.environ.get("LANG")
        or os.environ.get("LANGUAGE")
    )

    def __init__(self):

        self._event_loop_mode = "native"  # `native` for an OS event loop
        self._started = False  # whether the `eventLoop` property is permanently set
        self._launcher = (
            False  # set by opening windows to ensure app is launched soon after
        )

        self._windows = []
        self._frames = {}
        self._fps: int = 60

        # set the callback to use for event dispatch & rendering
        register(self._dispatch)  # type: ignore

        # track new windows and schedule launch if needed
        Window.events.on(WindowEvent.open, self.on_window_open)

        # drop closed windows
        Window.events.on(WindowEvent.close, self.on_window_close)

    @property
    def windows(self) -> List["Window"]:
        return self._windows.copy()

    @property
    def running(self) -> bool:
        return self._started

    @property
    def eventLoop(self) -> str:
        return self._event_loop_mode

    @eventLoop.setter
    def eventLoop(self, mode: str):
        if not self._started:
            raise RuntimeError("Cannot alter event loop after it has begun")
        if mode not in ("native",) and mode != self._event_loop_mode:
            self._event_loop_mode = set_mode(mode)  # type: ignore

    @property
    def fps(self) -> int:
        return self._fps

    @fps.setter
    def fps(self, rate: int):
        _check_support()
        if rate >= 1 and rate != self._fps:
            self._fps = set_rate(int(rate))  # type: ignore

    def launch(self):
        _check_support()
        self._started = True
        activate()  # type: ignore

    def wait_for_termination(self):
        wait_for_termination()  # type: ignore
        self._launcher = False
        self.emit(WindowEvent.idle, self, WindowEvent.idle)

    def quit(self):
        quit()  # type: ignore

    def _eachWindow(self, updates: dict, callback: Callable):
        for id, payload in updates.items():
            win = next((w for w in self._windows if w.id == int(id)), None)
            if win:
                callback(win, payload)

    def _dispatch(self, is_frame: bool, payload: str):

        def f1(win: "Window", data: Dict[str, Any]):
            win.left = win.left or data.get("left")
            win.top = win.top or data.get("top")

        def f2(win: "Window") -> bool:
            # keep active windows and new ones still waiting for a `geom` roundtrip to set their initial position
            if win.id in state or win.top is None:
                for k, v in state[win.id].items():
                    setattr(win, k, v)
                return True
            # but otherwise evict all windows that have been closed via title bar widget
            win.close()
            return False

        def f3(win: "Window", events: List[Dict[str, Any]]):
            pairs = [(k, v) for d in events for k, v in d.items()]
            for tp, e in pairs:
                _handle_ui_event(win, tp, e)

        d = json.loads(payload)
        geom = d.get("geom")
        state = d.get("state")
        ui = d.get("ui")

        # merge autogenerated window locations into newly opened windows
        if geom:
            self._eachWindow(geom, f1)

        # update state of windows that are still active and mark others as closed
        if state:
            self._windows = list(filter(f2, self._windows))

        # deliver ui events to corresponding windows
        if ui:
            self._eachWindow(ui, f3)

        # provide frame updates to prompt redraws
        if is_frame:
            for win in self._windows:
                frame = self._frames[win.id] + 1
                self._frames[win.id] = frame

                if frame == 0:
                    win.emit("setup")
                win.emit("frame", {"frame": frame})
                if win.listener_count("draw"):
                    win.canvas.getContext("2d").reset()
                    win.emit("draw", {"frame": frame})

        # if this is a full roundtrip, return window state & content
        return is_frame and [
            json.dumps(list(map(lambda w: w.state, self._windows))),
            list(map(lambda w: w.canvas.pages[w.page - 1].core(), self._windows)),
        ]

    def on_window_open(self, win: "Window"):
        self._windows.append(win)
        self._frames[win.id] = 0
        if not self._launcher:
            self._launcher = True
            self.launch()
        open_window(json.dumps(win.state), win.canvas.pages[win.page - 1].core())  # type: ignore

    def on_window_close(self, win: "Window"):
        self._windows = [w for w in self._windows if w.id != win.id]
        close_window(win.id)  # type: ignore
        win.emit(WindowEvent.close)


class WindowState(TypedDict):
    title: str
    visible: bool
    resizeable: bool
    borderless: bool
    background: str
    fullscreen: bool
    closed: bool
    page: int
    left: int | None
    top: int | None
    width: int
    height: int
    text_contrast: float
    text_gamma: float
    cursor: str
    fit: str
    id: int


class Window(EventEmitter):
    __slots__ = ("__canvas", "__state")

    events = EventEmitter()
    __kwargs = "id,left,top,width,height,title,page,background,fullscreen,cursor,fit,visible,resizable,borderless,closed".split(
        ","
    )
    __next_id = 1

    def __init__(
        self, width: int = 512, height: int = 512, opts: Dict[str, Any] | None = None
    ):
        _check_support()

        opts = opts or {}
        if not math.isfinite(width) or not math.isfinite(height):
            if opts.get("width"):
                width = opts["width"]
            elif opts.get("canvas"):
                width = opts["canvas"].width
            else:
                width = 512
            if opts.get("height"):
                height = opts["height"]
            elif opts.get("canvas"):
                height = opts["canvas"].height
            else:
                height = 512

        has_canvas = isinstance(opts.get("canvas"), Canvas)
        if has_canvas:
            canvas: Canvas = opts["canvas"]
            engine = canvas.engine
            text_contrast = engine.get("textContrast", 0)
            text_gamma = engine.get("textGamma", 1.4)
        else:
            text_contrast = opts.get("text_contrast", 0)
            text_gamma = opts.get("text_gamma", 1.4)
            canvas = Canvas(
                width,
                height,
                {"text_contrast": text_contrast, "text_gamma": text_gamma},
            )

        self.__canvas = canvas
        self.__state = WindowState(
            title="",
            visible=True,
            resizeable=True,
            borderless=False,
            background="white",
            fullscreen=False,
            closed=False,
            page=len(canvas.pages),
            left=None,
            top=None,
            width=width,
            height=height,
            text_contrast=text_contrast,
            text_gamma=text_gamma,
            cursor="default",
            fit="contain",
            id=Window.__next_id,
        )
        Window.__next_id += 1

        for k in Window.__kwargs:
            if k in opts:
                setattr(self, k, opts[k])

        Window.events.emit("open", self)

    @property
    def state(self) -> WindowState:
        return self.__state.copy()

    @property
    def ctx(self) -> CanvasRenderingContext2D:
        return self.__canvas.pages[self.page - 1]

    @property
    def id(self) -> int:
        return self.__state["id"]

    @id.setter
    def id(self, value: int):
        # 方便 setattr 调用，不用特地处理 id 参数，但实际上 id 是只读的，不能修改
        if value != self.id:
            raise ValueError(
                "Window ID is read-only and cannot be changed after creation"
            )

    @property
    def canvas(self) -> Canvas:
        return self.__canvas

    @canvas.setter
    def canvas(self, value: Canvas):
        if not isinstance(value, Canvas):
            raise ValueError("canvas must be an instance of Canvas")
        self.__canvas = value
        self.__state["page"] = len(value.pages)
        self.__state["text_contrast"] = value.engine["textContrast"]
        self.__state["text_gamma"] = value.engine["textGamma"]

    @property
    def visible(self) -> bool:
        return self.__state["visible"]

    @visible.setter
    def visible(self, value: bool):
        self.__state["visible"] = bool(value)

    @property
    def resizeable(self) -> bool:
        return self.__state["resizeable"]

    @resizeable.setter
    def resizeable(self, value: bool):
        self.__state["resizeable"] = bool(value)

    @property
    def borderless(self) -> bool:
        return self.__state["borderless"]

    @borderless.setter
    def borderless(self, value: bool):
        self.__state["borderless"] = bool(value)

    @property
    def fullscreen(self) -> bool:
        return self.__state["fullscreen"]

    @fullscreen.setter
    def fullscreen(self, value: bool):
        self.__state["fullscreen"] = bool(value)

    @property
    def title(self) -> str:
        return self.__state["title"]

    @title.setter
    def title(self, value: str):
        self.__state["title"] = str(value) if value is not None else ""

    @property
    def cursor(self) -> str:
        return self.__state["cursor"]

    @cursor.setter
    def cursor(self, value: str):
        if css.cursor(value):
            self.__state["cursor"] = value

    @property
    def fit(self) -> str:
        return self.__state["fit"]

    @fit.setter
    def fit(self, value: str):
        if css.fit(value):
            self.__state["fit"] = value

    @property
    def left(self) -> int | None:
        return self.__state["left"]

    @left.setter
    def left(self, value: int | None):
        if value is not None and math.isfinite(value):
            self.__state["left"] = value

    @property
    def top(self) -> int | None:
        return self.__state["top"]

    @top.setter
    def top(self, value: int | None):
        if value is not None and math.isfinite(value):
            self.__state["top"] = value

    @property
    def width(self) -> int:
        return self.__state["width"]

    @width.setter
    def width(self, value: int):
        if math.isfinite(value):
            self.__state["width"] = value

    @property
    def height(self) -> int:
        return self.__state["height"]

    @height.setter
    def height(self, value: int):
        if math.isfinite(value):
            self.__state["height"] = value

    @property
    def page(self) -> int:
        return self.__state["page"]

    @page.setter
    def page(self, value: int):
        if value < 0:
            value += len(self.__canvas.pages) + 1
        try:
            page = self.__canvas.pages[value - 1]
        except IndexError:
            # ignore invalid page number, keep current page
            return
        if self.__state["page"] != value:
            width, height = page.raw_size()
            self.canvas.raw_set_width(width)
            self.canvas.raw_set_height(height)
            self.__state["page"] = value

    @property
    def background(self) -> str:
        return self.__state["background"]

    @background.setter
    def background(self, value: str):
        self.__state["background"] = str(value) if value is not None else ""

    @property
    def closed(self) -> bool:
        return self.__state["closed"]

    def close(self):
        if not self.__state["closed"]:
            self.__state["closed"] = True
            Window.events.emit("close", self)

    def open(self):
        if self.__state["closed"]:
            self.__state["closed"] = False
            Window.events.emit("open", self)

    def emit(self, event: str, *args: Any, **kwargs):
        try:
            super().emit(event, self, event, *args, **kwargs)
        except Exception as e:
            # 捕获事件处理器中的异常，避免影响主流程
            print(f"Error in event handler for '{event}': {e}")


App = _App()
