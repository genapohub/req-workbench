// API 就绪网关：Mock 模式下，请求发出前等待 MSW worker 就绪（带超时兜底）；
// 真实后端模式（VITE_USE_MOCK=false）下不设置网关，立即放行。
let gate = Promise.resolve()

export function setApiGate(promise) {
  gate = promise
}

export function getApiGate() {
  return gate
}
