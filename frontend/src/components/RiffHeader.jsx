import PropTypes from 'prop-types'
import CIStatus from './CIStatus'

function RiffHeader({ riff, prStatus }) {
  return (
    <header className="mb-4">
      <div className="mb-4">
        <h1 className="text-3xl font-bold text-cyber-text font-mono mb-2">{riff.slug}</h1>
        {/* PR Status Subheading */}
        {prStatus && (
          <div className="space-y-1">
            <div className="flex items-center gap-3 text-sm font-mono">
              <a
                href={prStatus.html_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-400 hover:text-blue-300 transition-colors duration-200"
              >
                #{prStatus.number} {prStatus.title}
              </a>
              <span className={`${prStatus.draft ? 'text-gray-400' : 'text-green-400'}`}>
                {prStatus.draft ? '📝 Draft' : '🟢 Ready'}
              </span>
              {/* CI Status */}
              <CIStatus prStatus={prStatus} />
            </div>
            {/* Commit Info */}
            {(prStatus.commit_hash_short || prStatus.commit_message) && (
              <div className="flex items-center gap-2 text-xs font-mono text-gray-400">
                {prStatus.commit_hash_short && (
                  <span className="bg-gray-800 px-2 py-1 rounded text-gray-300">
                    {prStatus.commit_hash_short}
                  </span>
                )}
                {prStatus.commit_message && (
                  <span className="truncate max-w-md" title={prStatus.commit_message}>
                    {prStatus.commit_message}
                  </span>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </header>
  )
}

RiffHeader.propTypes = {
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
  })
}

export default RiffHeader