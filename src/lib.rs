//! SigmaOS-session-manager — Desktop session management for SigmaOS
#![allow(dead_code)]

pub mod config;
pub mod error;
pub mod file;
pub mod service;
pub mod theme;
pub mod window;

pub use config::Config;
pub use error::{ComponentError, Result};
pub use file::FileManager;
pub use service::Service;
pub use theme::{Color, ColorPalette, Theme, ThemeManager};
pub use window::{Rect, Window, WindowManager};

pub fn version() -> &'static str {
    env!("CARGO_PKG_VERSION")
}
