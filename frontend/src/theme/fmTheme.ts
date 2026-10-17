import { theme, type ThemeConfig } from 'antd'

/** Dark FM26 tokens — see project TZ §6.1 */
export const fmTheme: ThemeConfig = {
  algorithm: theme.darkAlgorithm,
  token: {
    colorPrimary: '#44d68a',
    colorSuccess: '#49aa19',
    colorWarning: '#d89614',
    colorError: '#dc4446',
    colorBgLayout: '#0d1217',
    colorBgContainer: '#151e25',
    colorBgElevated: '#1f2a32',
    colorText: 'rgba(255,255,255,0.85)',
    colorTextSecondary: 'rgba(255,255,255,0.45)',
    colorBorder: '#29353d',
    borderRadius: 8,
    fontSize: 14,
    fontFamily:
      "Inter, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
  },
  components: {
    Layout: {
      siderBg: '#101820',
      headerBg: '#11191f',
      bodyBg: '#0d1217',
      triggerBg: '#101820',
    },
    Menu: {
      darkItemBg: 'transparent',
      darkItemSelectedBg: '#193d31',
      darkItemSelectedColor: '#5ce29c',
      darkItemHoverBg: '#19242d',
      itemHeight: 43,
    },
    Card: {
      colorBgContainer: '#151e25',
      colorBorderSecondary: '#29353d',
    },
    Table: {
      headerBg: '#121a20',
      rowHoverBg: '#1c2b32',
    },
  },
}
