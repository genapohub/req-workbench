import { setupWorker } from 'msw/browser'
import { handlers } from './handlers'

export async function startMock() {
  const worker = setupWorker(...handlers)
  await worker.start({ onUnhandledRequest: 'bypass' })
  console.info('[MSW] mock worker started')
}
