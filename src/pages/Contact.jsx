import { useState } from 'react'
import { Card, Button, Input, PageHeader, Alert } from '../components/ui'
import Layout from '../components/Layout'

function Contact() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    message: ''
  })
  const [showSuccess, setShowSuccess] = useState(false)

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
    setShowSuccess(true)
    setFormData({ name: '', email: '', message: '' })
    
    // Hide success message after 5 seconds
    setTimeout(() => setShowSuccess(false), 5000)
  }

  return (
    <Layout>
      <PageHeader 
        title="Get in Touch" 
        subtitle="We'd love to hear from you. Send us a message and we'll respond as soon as possible."
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Contact Information */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold text-text-primary mb-6">Contact Information</h2>
          <div className="space-y-4">
            <div className="flex items-start space-x-3">
              <span className="text-2xl">📧</span>
              <div>
                <h3 className="font-medium text-text-primary">Email</h3>
                <p className="text-text-secondary">hello@openvibe.com</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <span className="text-2xl">🐙</span>
              <div>
                <h3 className="font-medium text-text-primary">GitHub</h3>
                <p className="text-text-secondary">github.com/openvibe</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <span className="text-2xl">🐦</span>
              <div>
                <h3 className="font-medium text-text-primary">Twitter</h3>
                <p className="text-text-secondary">@openvibe</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <span className="text-2xl">💼</span>
              <div>
                <h3 className="font-medium text-text-primary">LinkedIn</h3>
                <p className="text-text-secondary">linkedin.com/company/openvibe</p>
              </div>
            </div>
          </div>
        </Card>

        {/* Contact Form */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold text-text-primary mb-6">Send us a Message</h2>
          
          {showSuccess && (
            <Alert variant="success" className="mb-6">
              Thank you for your message! We'll get back to you soon.
            </Alert>
          )}
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Name"
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
            />
            <Input
              label="Email"
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
            />
            <div className="space-y-1">
              <label className="block text-sm font-medium text-text-primary">
                Message
              </label>
              <textarea
                name="message"
                rows="5"
                value={formData.message}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 bg-background-secondary border border-gray-600 rounded-lg text-text-primary placeholder-text-secondary focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-background-primary focus:ring-primary-300 focus:border-primary-300 hover:border-gray-500 transition-colors duration-200"
                placeholder="Your message..."
              />
            </div>
            <Button type="submit" className="w-full">
              Send Message
            </Button>
          </form>
        </Card>
      </div>
    </Layout>
  )
}

export default Contact