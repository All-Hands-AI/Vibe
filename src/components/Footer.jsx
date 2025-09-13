function Footer() {
  return (
    <footer className="bg-gray-850 border-t border-gray-700 mt-auto pt-8 pb-4">
      <div className="max-w-6xl mx-auto px-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
          <div>
            <h3 className="text-primary-300 text-2xl mb-4">OpenVibe</h3>
            <p className="text-gray-300 leading-relaxed">Building amazing experiences with React</p>
          </div>
          <div>
            <h4 className="text-primary-300 text-lg mb-4">Quick Links</h4>
            <ul className="list-none p-0 m-0">
              <li className="mb-2">
                <a href="/" className="text-gray-300 no-underline transition-colors duration-300 hover:text-primary-300">
                  Home
                </a>
              </li>
              <li className="mb-2">
                <a href="/about" className="text-gray-300 no-underline transition-colors duration-300 hover:text-primary-300">
                  About
                </a>
              </li>
              <li className="mb-2">
                <a href="/contact" className="text-gray-300 no-underline transition-colors duration-300 hover:text-primary-300">
                  Contact
                </a>
              </li>
            </ul>
          </div>
          <div>
            <h4 className="text-primary-300 text-lg mb-4">Connect</h4>
            <ul className="list-none p-0 m-0">
              <li className="mb-2">
                <a 
                  href="https://github.com" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-gray-300 no-underline transition-colors duration-300 hover:text-primary-300"
                >
                  GitHub
                </a>
              </li>
              <li className="mb-2">
                <a 
                  href="https://twitter.com" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-gray-300 no-underline transition-colors duration-300 hover:text-primary-300"
                >
                  Twitter
                </a>
              </li>
              <li className="mb-2">
                <a 
                  href="https://linkedin.com" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-gray-300 no-underline transition-colors duration-300 hover:text-primary-300"
                >
                  LinkedIn
                </a>
              </li>
            </ul>
          </div>
        </div>
        <div className="border-t border-gray-700 pt-4 text-center">
          <p className="text-gray-500 m-0 text-sm">&copy; 2025 OpenVibe. All rights reserved.</p>
        </div>
      </div>
    </footer>
  )
}

export default Footer