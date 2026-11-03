// See docs for instructions on this file:
// https://github.com/DefinitelyTyped/DefinitelyTyped/tree/master/types/react-table

import type { ReactNode } from 'react'
import {
  UseFiltersColumnOptions,
  UseFiltersColumnProps,
  UseFiltersInstanceProps,
  UseFiltersOptions,
  UseFiltersState,
  UseSortByColumnOptions,
  UseSortByColumnProps,
  UseSortByHooks,
  UseSortByInstanceProps,
  UseSortByOptions,
  UseSortByState,
} from 'react-table'

declare module 'react-table' {
  // take this file as-is, or comment out the sections that don't apply to your plugin configuration

  export interface TableOptions<D extends object>
    extends UseFiltersOptions<D>, UseSortByOptions<D> {}

  export interface Hooks<D extends object = {}> extends UseSortByHooks<D> {}

  export interface TableInstance<D extends object = {}>
    extends UseFiltersInstanceProps<D>, UseSortByInstanceProps<D> {}

  export interface TableState<D extends object = {}>
    extends UseFiltersState<D>, UseSortByState<D> {}

  export interface ColumnInterface<D extends object = {}>
    extends UseFiltersColumnOptions<D>, UseSortByColumnOptions<D> {
    // Rendered in the header cell under the column's title, outside the sort
    // toggle, for controls that apply to the column
    subHeader?: ReactNode
  }

  export interface ColumnInstance<D extends object = {}>
    extends UseFiltersColumnProps<D>, UseSortByColumnProps<D> {}

  export interface Cell<D extends object = {}, V = any> {}

  export interface Row<D extends object = {}> {}
}
