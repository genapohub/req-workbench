import { chromium } from '@playwright/test'

const url = process.env.SMOKE_URL || 'http://127.0.0.1:5175/login'
const chromePath = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
const browser = await chromium.launch({ executablePath: chromePath, headless: true })
const page = await browser.newPage()
const errors = []
page.on('pageerror', (err) => errors.push(String(err.message || err)))
page.on('console', (msg) => {
  const text = msg.text()
  if (msg.type() === 'error' && /insertBefore|渲染错误|TypeError|ReferenceError|SyntaxError|\[App\]|\[Router\]/.test(text)) {
    errors.push(text)
  }
})
await page.goto(url, { waitUntil: 'networkidle', timeout: 20000 })
await page.waitForSelector('text=登录', { timeout: 10000 })
await page.waitForSelector('text=先补齐业务基座', { timeout: 10000 })
const body = await page.textContent('body')
if (body?.includes('页面渲染出现问题') || body?.includes('insertBefore')) {
  throw new Error('页面仍显示渲染错误：' + body.slice(0, 200))
}
if (errors.length) {
  throw new Error('浏览器控制台错误：' + errors.join('\n'))
}
await browser.close()
console.log('Mock 登录页验收通过：', url)
