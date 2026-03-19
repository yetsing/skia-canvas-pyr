#![allow(unused_imports)]
#![allow(unused_variables)]
#![allow(dead_code)]
use pyo3::prelude::*;

use std::sync::{Mutex, OnceLock, mpsc};
use std::thread;

use crate::context::Context2D;
use crate::gpu::RenderingEngine;
use crate::utils::*;

pub mod app;
use app::{App, LoopMode};

pub mod window;
use window::WindowSpec;

pub mod event;

pub mod window_mgr;

/// 单个全局槽。启动时会覆盖旧的 slot（如果旧任务存在且没有被等待，则旧 receiver 会被丢弃）
static SLOT: OnceLock<Mutex<Option<mpsc::Receiver<()>>>> = OnceLock::new();

fn slot() -> &'static Mutex<Option<mpsc::Receiver<()>>> {
  SLOT.get_or_init(|| Mutex::new(None))
}

fn validate_gpu() -> PyResult<()> {
  // bail out if we can't draw to the screen
  if let Some(reason) = RenderingEngine::default().lacks_gpu_support() {
    return Err(pyo3::exceptions::PyRuntimeError::new_err(reason));
  }
  Ok(())
}

#[pyfunction]
pub fn register(arg: Bound<'_, PyAny>) {
  App::register(arg.unbind());
}

#[pyfunction]
pub fn activate() -> PyResult<()> {
  validate_gpu()?;

  let (tx, rx) = mpsc::channel::<()>();
  {
    let mut s = slot().lock().unwrap();
    *s = Some(rx); // 覆盖前一个（如果存在）
  }

  App::activate(tx);

  Ok(())
}

#[pyfunction]
pub fn set_rate(fps: i32) -> PyResult<i32> {
  App::set_fps(fps);
  Ok(fps)
}

#[pyfunction]
pub fn set_mode(mode: String) -> PyResult<String> {
  let loop_mode = match mode.as_str() {
    "native" => LoopMode::Native,
    _ => {
      return Err(pyo3::exceptions::PyValueError::new_err(format!(
        "Invalid event loop mode: {}",
        mode
      )));
    }
  };

  App::set_mode(loop_mode);
  Ok(mode)
}

#[pyfunction(name = "open_window")]
pub fn open(win_config: String, context: &Context2D) -> PyResult<()> {
  let spec = serde_json::from_str::<WindowSpec>(&win_config).expect("Invalid window state");

  validate_gpu()?;

  App::open_window(spec, context.get_page());
  Ok(())
}

#[pyfunction(name = "close_window")]
pub fn close(id: u32) {
  App::close_window(id);
}

#[pyfunction]
pub fn quit() {
  App::quit();
}

#[pyfunction]
pub fn wait_for_termination() -> PyResult<()> {
  let rx_opt = {
    let mut s = slot().lock().unwrap();
    s.take() // 取出并置空
  };

  match rx_opt {
    Some(rx) => rx
      .recv()
      .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("recv error: {}", e))),
    None => Err(pyo3::exceptions::PyRuntimeError::new_err("no task started")),
  }?;

  Ok(())
}
