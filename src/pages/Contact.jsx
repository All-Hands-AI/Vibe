import { useState } from 'react'

function Contact() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    message: ''
  })

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    // In a real app, you would send this data to a server
    console.log('Form submitted:', formData)
    alert('🔥 Message transmitted to the mainframe! We\'ll hack back to you soon. 💻')
    setFormData({ name: '', email: '', message: '' })
  }

  return (
    <div className="min-h-screen bg-black text-neon-green relative">
      <div className="max-w-6xl mx-auto px-8 py-16 relative z-10">
        <section className="text-center mb-16">
          <h1 className="text-5xl font-bold text-neon-green mb-4 font-mono neon-glow-strong glitch-text" data-text="Get in Touch">
            <span className="text-neon-cyan">{'<'}</span> Get in Touch <span className="text-neon-cyan">{'/>'}</span>
            <span className="animate-terminal-blink">_</span>
          </h1>
          <p className="text-xl text-neon-green/80 max-w-2xl mx-auto font-mono">
            📡 We'd love to hear from you. Send us a message and we'll hack back as soon as possible.
          </p>
        </section>

        <section>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
            <div>
              <h2 className="text-3xl font-bold text-neon-green mb-8 font-mono neon-glow">
                📞 Contact Information
              </h2>
              <div className="space-y-6">
                <div className="hacker-card group">
                  <h3 className="text-xl font-semibold text-neon-green mb-2 font-mono neon-glow group-hover:animate-pulse-neon">
                    📧 Email
                  </h3>
                  <p className="text-neon-green/80 font-mono">hello@openvibe.com</p>
                </div>
                <div className="hacker-card group">
                  <h3 className="text-xl font-semibold text-neon-green mb-2 font-mono neon-glow group-hover:animate-pulse-neon">
                    🐙 GitHub
                  </h3>
                  <p className="text-neon-green/80 font-mono">github.com/openvibe</p>
                </div>
                <div className="hacker-card group">
                  <h3 className="text-xl font-semibold text-neon-green mb-2 font-mono neon-glow group-hover:animate-pulse-neon">
                    🐦 Twitter
                  </h3>
                  <p className="text-neon-green/80 font-mono">@openvibe</p>
                </div>
                <div className="hacker-card group">
                  <h3 className="text-xl font-semibold text-neon-green mb-2 font-mono neon-glow group-hover:animate-pulse-neon">
                    💼 LinkedIn
                  </h3>
                  <p className="text-neon-green/80 font-mono">linkedin.com/company/openvibe</p>
                </div>
              </div>
            </div>

            <div className="terminal-window">
              <div className="terminal-header">
                💻 MESSAGE_FORM.EXE
              </div>
              <div className="terminal-content">
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div>
                    <label htmlFor="name" className="block text-sm font-medium text-neon-green mb-2 font-mono">
                      <span className="text-neon-cyan">{'>'}</span> Name:
                    </label>
                    <input
                      type="text"
                      id="name"
                      name="name"
                      value={formData.name}
                      onChange={handleChange}
                      required
                      className="w-full px-4 py-3 bg-black text-neon-green font-mono border-2 border-neon-green/30 focus:outline-none focus:border-neon-green focus:neon-glow transition-all duration-200"
                      placeholder="Enter your hacker alias..."
                    />
                  </div>
                  <div>
                    <label htmlFor="email" className="block text-sm font-medium text-neon-green mb-2 font-mono">
                      <span className="text-neon-cyan">{'>'}</span> Email:
                    </label>
                    <input
                      type="email"
                      id="email"
                      name="email"
                      value={formData.email}
                      onChange={handleChange}
                      required
                      className="w-full px-4 py-3 bg-black text-neon-green font-mono border-2 border-neon-green/30 focus:outline-none focus:border-neon-green focus:neon-glow transition-all duration-200"
                      placeholder="your.email@cybernet.com"
                    />
                  </div>
                  <div>
                    <label htmlFor="message" className="block text-sm font-medium text-neon-green mb-2 font-mono">
                      <span className="text-neon-cyan">{'>'}</span> Message:
                    </label>
                    <textarea
                      id="message"
                      name="message"
                      rows="5"
                      value={formData.message}
                      onChange={handleChange}
                      required
                      className="w-full px-4 py-3 bg-black text-neon-green font-mono border-2 border-neon-green/30 focus:outline-none focus:border-neon-green focus:neon-glow transition-all duration-200 resize-vertical"
                      placeholder="Enter your cyberpunk message..."
                    ></textarea>
                  </div>
                  <button 
                    type="submit" 
                    className="btn-hacker-primary w-full text-base"
                  >
                    🚀 Transmit Message
                  </button>
                </form>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}

export default Contact