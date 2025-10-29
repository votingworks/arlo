import React from 'react'

export interface Timing {
  defaultRefetchInterval: number
  modalDismissDelay: number
}

export const DEFAULT_TIMING: Timing = {
  defaultRefetchInterval: 1000,
  modalDismissDelay: 1500,
}

export const TEST_TIMING: Timing = {
  defaultRefetchInterval: 1,
  modalDismissDelay: 1,
}

export const TimingContext = React.createContext<Timing>(DEFAULT_TIMING)

export function useTiming(): Timing {
  return React.useContext(TimingContext)
}
