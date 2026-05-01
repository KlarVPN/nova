import type { Config } from 'prettier'

const config: Config = {
  semi: false,
  singleQuote: true,
  tabWidth: 2,
  trailingComma: 'all',
  printWidth: 100,
  plugins: ['prettier-plugin-tailwindcss', 'prettier-plugin-organize-imports'],
}

export default config
