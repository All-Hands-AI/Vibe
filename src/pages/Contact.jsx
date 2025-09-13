import { useState } from 'react'
import './Contact.css'

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
    <div className="contact">
      <div className="container">
        <section className="contact-hero">
          <h1>Get in Touch</h1>
          <p>We&apos;d love to hear from you. Send us a message and we&apos;ll respond as soon as possible.</p>
        </section>

        <section className="contact-content">
          <div className="contact-grid">
            <div className="contact-info">
              <h2>Contact Information</h2>
              <div className="contact-item">
                <h3>📧 Email</h3>
                <p>hello@openvibe.com</p>
              </div>
              <div className="contact-item">
                <h3>🐙 GitHub</h3>
                <p>github.com/openvibe</p>
              </div>
              <div className="contact-item">
                <h3>🐦 Twitter</h3>
                <p>@openvibe</p>
              </div>
              <div className="contact-item">
                <h3>💼 LinkedIn</h3>
                <p>linkedin.com/company/openvibe</p>
              </div>
            </div>

            <div className="contact-form-container">
              <form className="contact-form" onSubmit={handleSubmit}>
                <div className="form-group">
                  <label htmlFor="name">Name</label>
                  <input
                    type="text"
                    id="name"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="email">Email</label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="message">Message</label>
                  <textarea
                    id="message"
                    name="message"
                    rows="5"
                    value={formData.message}
                    onChange={handleChange}
                    required
                  ></textarea>
                </div>
                <button type="submit" className="btn btn-primary">Send Message</button>
              </form>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}

export default Contact