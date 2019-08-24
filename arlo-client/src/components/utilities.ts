export const api = async <T>(endpoint: string, options: any): Promise<T> => {
  const apiBaseURL = ''
  const res = await fetch(apiBaseURL + endpoint, options)
  if (!res.ok) {
    throw new Error(res.statusText)
  }
  return res.json() as Promise<T>
}

export default api
