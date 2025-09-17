import PropTypes from 'prop-types'
import ChatWindow from './ChatWindow'
import RiffNavigation from './RiffNavigation'
import RiffHeader from './RiffHeader'
import DeploymentStatus from './DeploymentStatus'

function RiffSidebar({ 
  app, 
  riff, 
  prStatus, 
  deploymentStatus, 
  userUUID 
}) {
  return (
    <div className="flex-1 lg:w-1/2 flex flex-col min-h-0">
      {/* Details Section with Padding */}
      <div className="p-4 flex-shrink-0">
        <RiffNavigation appSlug={app.slug} riffSlug={riff.slug} />
        <RiffHeader riff={riff} prStatus={prStatus} />
        <DeploymentStatus 
          deploymentStatus={deploymentStatus} 
          appSlug={app.slug} 
          riffSlug={riff.slug} 
        />
      </div>

      {/* Chat Window - Flexible Height */}
      <div className="flex-1 min-h-0">
        {userUUID ? (
          <ChatWindow 
            app={app} 
            riff={riff} 
            userUuid={userUUID} 
          />
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="w-8 h-8 border-4 border-gray-600 border-t-cyber-muted rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-cyber-muted">Initializing chat...</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

RiffSidebar.propTypes = {
  app: PropTypes.shape({
    slug: PropTypes.string.isRequired
  }).isRequired,
  riff: PropTypes.shape({
    slug: PropTypes.string.isRequired
  }).isRequired,
  prStatus: PropTypes.shape({
    html_url: PropTypes.string,
    number: PropTypes.number,
    title: PropTypes.string,
    draft: PropTypes.bool,
    commit_hash_short: PropTypes.string,
    commit_message: PropTypes.string
  }),
  deploymentStatus: PropTypes.shape({
    status: PropTypes.string,
    details: PropTypes.shape({
      workflow_url: PropTypes.string
    })
  }),
  userUUID: PropTypes.string
}

export default RiffSidebar