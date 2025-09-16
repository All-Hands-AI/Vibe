import { useEffect } from 'react'

/**
 * Custom hook to update the document title
 * @param {string} title - The title to set for the document
 */
export function useDocumentTitle(title) {
  useEffect(() => {
    if (title) {
      document.title = title
    }
  }, [title])
}

/**
 * Helper function to format page titles consistently
 * @param {string} pageType - The type of page ('apps', 'app', 'riff')
 * @param {string} appName - The name of the app (optional)
 * @param {string} riffName - The name of the riff (optional)
 * @returns {string} Formatted title
 */
export function formatPageTitle(pageType, appName = null, riffName = null) {
  const baseTitle = 'openvibe'
  
  switch (pageType) {
    case 'apps':
      return `Apps - ${baseTitle}`
    case 'app':
      return appName ? `App: ${appName} - ${baseTitle}` : `App - ${baseTitle}`
    case 'riff':
      if (appName && riffName) {
        return `Riff: ${appName}/${riffName} - ${baseTitle}`
      } else if (appName) {
        return `App: ${appName} - ${baseTitle}`
      }
      return `Riff - ${baseTitle}`
    default:
      return baseTitle
  }
}