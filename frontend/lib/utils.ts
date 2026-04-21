/**
 * Utility function to merge class names conditionally
 * Similar to clsx or classnames library
 */
export function cn(...classes: (string | false | null | undefined)[]): string {
  return classes.filter(Boolean).join(' ')
}
