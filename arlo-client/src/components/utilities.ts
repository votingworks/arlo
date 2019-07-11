export const api = <T>(endpoint: string, options: any): Promise<T> => {
  const apiBaseURL = ''
  return fetch(apiBaseURL + endpoint, options).then(res => {
    if (!res.ok) {
      throw new Error(res.statusText)
    }
    return res.json() as Promise<T>
  })
}

export default api
