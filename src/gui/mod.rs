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
pub fn run_event_loop() -> PyResult<()> {
  validate_gpu()?;
  App::run_event_loop();
  Ok(())
}
