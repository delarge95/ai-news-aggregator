/**
 * Navigation utility functions
 */

/**
 * Update the page title
 * @param title - The new page title
 */
export function updatePageTitle(title: string): void {
  document.title = title ? `${title} | AI News Aggregator` : 'AI News Aggregator';
}

/**
 * Scroll to the top of the page smoothly
 */
export function scrollToTop(): void {
  window.scrollTo({
    top: 0,
    behavior: 'smooth'
  });
}

/**
 * Scroll to a specific element
 * @param elementId - The ID of the element to scroll to
 */
export function scrollToElement(elementId: string): void {
  const element = document.getElementById(elementId);
  if (element) {
    element.scrollIntoView({
      behavior: 'smooth',
      block: 'start'
    });
  }
}

/**
 * Check if an element is in viewport
 * @param element - The element to check
 * @returns true if element is in viewport
 */
export function isInViewport(element: HTMLElement): boolean {
  const rect = element.getBoundingClientRect();
  return (
    rect.top >= 0 &&
    rect.left >= 0 &&
    rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
    rect.right <= (window.innerWidth || document.documentElement.clientWidth)
  );
}

/**
 * Get current scroll position
 * @returns Current scroll Y position
 */
export function getScrollPosition(): number {
  return window.pageYOffset || document.documentElement.scrollTop;
}

/**
 * Navigate to a route programmatically
 * @param path - The path to navigate to
 */
export function navigateTo(path: string): void {
  window.history.pushState({}, '', path);
  window.dispatchEvent(new PopStateEvent('popstate'));
}
