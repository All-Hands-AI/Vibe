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
    alert('Thank you for your message! We&apos;ll get back to you soon.')
    setFormData({ name: '', email: '', message: '' })
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="max-w-6xl mx-auto px-8 py-16">
        <section className="text-center mb-16">
          <h1 className="text-5xl font-bold text-primary-300 mb-4">Get in Touch</h1>
          <p className="text-xl text-gray-300 max-w-2xl mx-auto">We&apos;d love to hear from you. Send us a message and we&apos;ll respond as soon as possible.</p>
        </section>

        <section>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
            <div>
              <h2 className="text-3xl font-bold text-primary-300 mb-8">Contact Information</h2>
              <div className="space-y-6">
                <div className="bg-gray-850 p-6 rounded-lg border border-gray-700">
                  <h3 className="text-xl font-semibold text-primary-300 mb-2">📧 Email</h3>
                  <p className="text-gray-300">hello@openvibe.com</p>
                </div>
                <div className="bg-gray-850 p-6 rounded-lg border border-gray-700">
                  <h3 className="text-xl font-semibold text-primary-300 mb-2">🐙 GitHub</h3>
                  <p className="text-gray-300">github.com/openvibe</p>
                </div>
                <div className="bg-gray-850 p-6 rounded-lg border border-gray-700">
                  <h3 className="text-xl font-semibold text-primary-300 mb-2">🐦 Twitter</h3>
                  <p className="text-gray-300">@openvibe</p>
                </div>
                <div className="bg-gray-850 p-6 rounded-lg border border-gray-700">
                  <h3 className="text-xl font-semibold text-primary-300 mb-2">💼 LinkedIn</h3>
                  <p className="text-gray-300">linkedin.com/company/openvibe</p>
                </div>
              </div>
            </div>

            <div className="bg-gray-850 p-8 rounded-lg border border-gray-700">
              <form onSubmit={handleSubmit} className="space-y-6">
                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-gray-300 mb-2">Name</label>
                  <input
                    type="text"
                    id="name"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    required
                    className="w-full px-4 py-3 bg-gray-700 text-white rounded-md border border-gray-600 focus:outline-none focus:ring-2 focus:ring-primary-300 focus:border-transparent transition-colors duration-200"
                  />
                </div>
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-2">Email</label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    required
                    className="w-full px-4 py-3 bg-gray-700 text-white rounded-md border border-gray-600 focus:outline-none focus:ring-2 focus:ring-primary-300 focus:border-transparent transition-colors duration-200"
                  />
                </div>
                <div>
                  <label htmlFor="message" className="block text-sm font-medium text-gray-300 mb-2">Message</label>
                  <textarea
                    id="message"
                    name="message"
                    rows="5"
                    value={formData.message}
                    onChange={handleChange}
                    required
                    className="w-full px-4 py-3 bg-gray-700 text-white rounded-md border border-gray-600 focus:outline-none focus:ring-2 focus:ring-primary-300 focus:border-transparent transition-colors duration-200 resize-vertical"
                  ></textarea>
                </div>
                <button 
                  type="submit" 
                  className="w-full px-6 py-3 bg-primary-300 text-gray-900 rounded-md font-semibold hover:bg-primary-400 transition-all duration-300 hover:transform hover:-translate-y-0.5"
                >
                  Send Message
                </button>
              </form>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}

export default Contact