import { useHistory, useLocation } from 'react-router-dom'
import { useMemo, useCallback } from 'react'

type SearchParams = Record<string, string | undefined>

const useSearchParams = <T extends SearchParams>(): [
  T | undefined,
  (newState: T) => void
] => {
  const history = useHistory()
  const { search } = useLocation()

  const searchParams = useMemo(
    () => Object.fromEntries(new URLSearchParams(search)) as T | undefined,
    [search]
  )

  const setSearchParams = useCallback(
    (newParams: SearchParams) => {
      const params = new URLSearchParams(
        Object.entries(newParams).filter(
          (entry): entry is [string, string] => entry[1] !== undefined
        )
      )
      history.replace({ search: params.toString() })
    },
    [history]
  )

  return [searchParams, setSearchParams]
}

export default useSearchParams
