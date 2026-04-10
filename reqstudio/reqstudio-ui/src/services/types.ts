/**
 * Shared API response types used across service modules.
 */

/** Generic paginated list envelope returned by list endpoints. */
export interface PaginatedList<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}
