import { theme, type ThemeConfig } from 'antd'

/** Dark FM26 + Sports.ru editorial red — see Figma Make UzmpQFpuRPpKjUFObZcVnj */
export const fmTheme: ThemeConfig = {
  algorithm: theme.darkAlgorithm,
  token: {
    colorPrimary: '#e82032',
    colorSuccess: '#49aa19',
    colorWarning: '#f1ae2a',
    colorError: '#e82032',
    colorLink: '#ff5866',
    colorBgLayout: '#101113',
    colorBgContainer: 'rgba(26,27,30,0.88)',
    colorBgElevated: '#202125',
    colorText: '#f4f5f6',
    colorTextSecondary: '#acadb1',
    colorBorder: 'rgba(255,255,255,0.14)',
    borderRadius: 5,
    fontSize: 14,
    fontFamily:
      "'Manrope', system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
  },
  components: {
    Layout: {
      siderBg: 'rgba(17,18,20,0.92)',
      headerBg: 'rgba(20,21,23,0.72)',
      bodyBg: 'transparent',
      triggerBg: 'rgba(17,18,20,0.92)',
    },
    Menu: {
      darkItemBg: 'transparent',
      darkItemSelectedBg: '#e82032',
      darkItemSelectedColor: '#ffffff',
      darkItemHoverBg: 'rgba(255,255,255,0.09)',
      darkItemColor: '#c4c5c8',
      itemHeight: 43,
      itemMarginBlock: 3,
      itemMarginInline: 4,
      itemPaddingInline: 12,
      itemBorderRadius: 4,
    },
    Card: {
      colorBgContainer: 'rgba(26,27,30,0.88)',
      colorBorderSecondary: 'rgba(255,255,255,0.14)',
    },
    Table: {
      headerBg: 'rgba(15,16,18,0.78)',
      rowHoverBg: 'rgba(255,255,255,0.04)',
    },
    Button: {
      primaryColor: '#ffffff',
      defaultBg: 'rgba(34,35,38,0.82)',
      defaultBorderColor: 'rgba(255,255,255,0.2)',
      defaultColor: '#f2f2f3',
      borderRadius: 3,
    },
    Segmented: {
      itemSelectedBg: '#e82032',
      itemSelectedColor: '#ffffff',
      trackBg: 'rgba(24,25,28,0.9)',
    },
    Modal: {
      contentBg: '#202125',
      headerBg: '#202125',
    },
  },
}
