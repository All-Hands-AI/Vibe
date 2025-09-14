import PropTypes from 'prop-types'

function FirstRiffModal({ isOpen, onClose, appName }) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="bg-black border-2 border-cyber-border rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <div className="text-3xl">🚀</div>
              <h2 className="text-2xl font-bold text-cyber-text font-mono">
                Welcome to Your First Riff!
              </h2>
            </div>
            <button
              onClick={onClose}
              className="text-cyber-muted hover:text-cyber-text text-2xl font-bold transition-colors duration-200"
              aria-label="Close modal"
            >
              ×
            </button>
          </div>

          {/* Content */}
          <div className="space-y-4 text-cyber-text font-mono">
            <div className="bg-cyber-bg border border-cyber-border rounded-lg p-4">
              <h3 className="text-lg font-semibold text-neon-green mb-2">
                🎯 What&apos;s happening now?
              </h3>
              <p className="text-cyber-muted leading-relaxed">
                This is your first &quot;riff&quot; for <span className="text-neon-green font-semibold">{appName}</span> - 
                think of it as the first change or iteration of your app. The AI agent is currently setting up 
                your app template and customizing it with your chosen name.
              </p>
            </div>

            <div className="bg-cyber-bg border border-cyber-border rounded-lg p-4">
              <h3 className="text-lg font-semibold text-neon-green mb-2">
                ⏱️ Timeline
              </h3>
              <div className="space-y-2 text-cyber-muted">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-neon-green rounded-full animate-pulse"></div>
                  <span>Agent is working (~5 minutes)</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-cyber-border rounded-full"></div>
                  <span>App deployment (~1-2 minutes)</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-cyber-border rounded-full"></div>
                  <span>Your app will appear in the iframe</span>
                </div>
              </div>
            </div>

            <div className="bg-cyber-bg border border-cyber-border rounded-lg p-4">
              <h3 className="text-lg font-semibold text-neon-green mb-2">
                💬 What can you do?
              </h3>
              <p className="text-cyber-muted leading-relaxed">
                You can chat with the AI agent in real-time to see its progress, ask questions, 
                or request additional changes. The agent will keep you updated as it works through 
                the setup process.
              </p>
            </div>

            <div className="bg-yellow-900/20 border border-yellow-500 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-yellow-400 mb-2">
                ℹ️ Pro Tip
              </h3>
              <p className="text-yellow-200 leading-relaxed">
                Once the agent finishes and pushes its work, you&apos;ll see your customized app 
                running live in the preview pane. This is where the magic happens!
              </p>
            </div>
          </div>

          {/* Footer */}
          <div className="mt-6 flex justify-end">
            <button
              onClick={onClose}
              className="btn-hacker-primary px-6 py-2"
            >
              Got it! Let&apos;s go 🎉
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

FirstRiffModal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  appName: PropTypes.string.isRequired
}

export default FirstRiffModal