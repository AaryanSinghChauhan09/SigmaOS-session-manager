use anyhow::Result;
use sigmaos_desktop_component::{Config, Service, ThemeManager, Theme, WindowManager, Rect};

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_config_process_aaa() -> Result<()> {
        let config = Config::default();
        assert!(config.process().is_ok());
        Ok(())
    }

    #[test]
    fn test_service_lifecycle_aaa() -> Result<()> {
        let config = Config::default();
        let mut service = Service::new(config);
        assert!(!service.is_running());
        service.start()?;
        assert!(service.is_running());
        assert!(service.start().is_err());
        service.stop()?;
        assert!(!service.is_running());
        assert!(service.stop().is_err());
        Ok(())
    }

    #[test]
    fn test_window_manager_aaa() -> Result<()> {
        let mut wm = WindowManager::new();
        let rect = Rect::new(0, 0, 800, 600);
        let id = wm.create_window("Session Window".to_string(), rect);
        assert!(wm.focus_window(id).is_ok());
        Ok(())
    }

    #[test]
    fn test_theme_manager_aaa() -> Result<()> {
        let mut tm = ThemeManager::new();
        let theme = Theme::new("DarkTheme".to_string());
        tm.add_theme(theme);
        assert!(tm.set_current_theme("DarkTheme").is_ok());
        Ok(())
    }
}
