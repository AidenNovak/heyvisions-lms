export const CURATED_FONTS = [
  'Albert Sans',
  'Barlow',
  'Cabin',
  'DM Sans',
  'Exo 2',
  'Figtree',
  'Fira Sans',
  'Geist',
  'IBM Plex Sans',
  'Instrument Sans',
  'Inter',
  'Josefin Sans',
  'Karla',
  'Lato',
  'Lexend',
  'Libre Franklin',
  'Manrope',
  'Montserrat',
  'Mulish',
  'Noto Sans',
  'Nunito',
  'Onest',
  'Open Sans',
  'Outfit',
  'Overpass',
  'Plus Jakarta Sans',
  'Poppins',
  'PT Sans',
  'Quicksand',
  'Raleway',
  'Red Hat Display',
  'Roboto',
  'Rubik',
  'Source Sans 3',
  'Sora',
  'Space Grotesk',
  'Titillium Web',
  'Urbanist',
  'Wix Madefor Text',
  'Work Sans',
]

// 平台默认字体（`--font-default`，见 app/layout.tsx 的 next/font 声明）。
// 这个常量同时是「未选择自定义字体」的哨兵值：组织配置里 font 为空或等于它时，
// 走平台默认而不是去 Google Fonts 额外加载。
export const DEFAULT_FONT = 'Geist'

export function getGoogleFontUrl(fontFamily: string): string {
  const encoded = fontFamily.replace(/ /g, '+')
  return `https://fonts.googleapis.com/css2?family=${encoded}:wght@400;500;600;700&display=swap`
}

export function getGoogleFontPreviewUrl(fontFamily: string): string {
  const encoded = fontFamily.replace(/ /g, '+')
  return `https://fonts.googleapis.com/css2?family=${encoded}:wght@400;700&display=swap`
}
