import { forwardRef } from 'react'
import PropTypes from 'prop-types'

const RiffIframe = forwardRef(({ appSlug, riffSlug }, ref) => {
  return (
    <div className="flex-1 lg:w-1/2 min-h-0">
      <div className="h-full overflow-hidden">
        <iframe
          ref={ref}
          src={`https://${appSlug}-${riffSlug}.fly.dev`}
          className="w-full h-full"
          title="Live App Preview"
          sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-popups-to-escape-sandbox"
        />
      </div>
    </div>
  )
})

RiffIframe.displayName = 'RiffIframe'

RiffIframe.propTypes = {
  appSlug: PropTypes.string.isRequired,
  riffSlug: PropTypes.string.isRequired
}

export default RiffIframe