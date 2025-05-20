import { useState, useRef, useEffect } from "react"
import { FiUpload, FiSend } from "react-icons/fi"
import axios from "axios"
import "./App.css"
import logo from "./assets/logo.png"
import botAvatar from "./assets/avtar.png"
import ReactMarkdown from 'react-markdown';
function formatAnswer(text) {
  // Return the full text without truncation to match the design in the image
  return <ReactMarkdown >{text}</ReactMarkdown>
}

function App() {
  const [file, setFile] = useState(null)
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState("")
  const [documentId, setDocumentId] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isResponding, setIsResponding] = useState(false)
  const fileInputRef = useRef(null)
  const messagesEndRef = useRef(null)
  const [toast, setToast] = useState(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isResponding])

  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 3000)
      return () => clearTimeout(timer)
    }
  }, [toast])

  const handleFileUpload = async (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile && selectedFile.type === "application/pdf") {
      setFile(selectedFile)
      const formData = new FormData()
      formData.append("file", selectedFile)
      try {
        setIsLoading(true)
        const response = await axios.post("http://localhost:8000/upload-pdf", formData)
        setDocumentId(response.data.document_id)
        setToast({ type: "success", message: "PDF Uploaded. You can now ask questions." })
      } catch (error) {
        setToast({ type: "error", message: "Failed to upload PDF." })
      } finally {
        setIsLoading(false)
      }
    } else {
      setToast({ type: "error", message: "Please upload a PDF file." })
    }
  }

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || !documentId) return
    const userMessage = inputMessage
    setInputMessage("")
    setMessages((prev) => [...prev, { role: "user", content: userMessage }])
    try {
      setIsResponding(true)
      const response = await axios.get(`http://localhost:8000/ask-question`, {
        params: {
          question: userMessage,
          document_id: documentId,
        },
      })
      setMessages((prev) => [...prev, { role: "assistant", content: response.data.answer }])
    } catch (error) {
      setToast({ type: "error", message: "Failed to get answer." })
    } finally {
      setIsResponding(false)
    }
  }

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="logo-container">
          <img src={logo || "/placeholder.svg"} alt="Planet" className="logo" />
        </div>
        <div className="header-actions">
          {file && (
            <div className="file-indicator">
              <span className="file-icon">📄</span>
              <span className="file-name">{file.name}</span>
            </div>
          )}
          <button className="upload-button" onClick={() => fileInputRef.current?.click()} disabled={isLoading}>
            {isLoading ? <span className="loader"></span> : <FiUpload className="upload-icon" />}
            <span>Upload PDF</span>
          </button>
          <input type="file" ref={fileInputRef} onChange={handleFileUpload} accept=".pdf" style={{ display: "none" }} />
        </div>
      </header>

      <div className="chat-container">
        <div className="messages-container">
          {messages.map((message, index) => (
            <div key={index} className={`message ${message.role === "user" ? "user-message" : "assistant-message"}`}>
              <div className="message-avatar">
                {message.role === "assistant" ? (
                  <img src={botAvatar || "/placeholder.svg"} alt="AI" className="bot-avatar" />
                ) : (
                  <div className="user-avatar">S</div>
                )}
              </div>
              <div className="message-content">
                {message.role === "assistant" ? formatAnswer(message.content) : message.content}
              </div>
            </div>
          ))}
          {isResponding && (
            <div className="message assistant-message">
              <div className="message-avatar">
                <img src={botAvatar || "/placeholder.svg"} alt="AI" className="bot-avatar" />
              </div>
              <div className="message-content">
                <span className="typing-indicator">Thinking...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-container">
          <input
            type="text"
            className="message-input"
            placeholder="Send a message..."
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            disabled={!documentId || isLoading || isResponding}
            onKeyPress={(e) => e.key === "Enter" && handleSendMessage()}
          />
          <button
            className="send-button"
            onClick={handleSendMessage}
            disabled={!documentId || isLoading || isResponding || !inputMessage.trim()}
          >
            <FiSend className="send-icon" />
          </button>
        </div>
      </div>

      {toast && <div className={`toast ${toast.type}`}>{toast.message}</div>}
    </div>
  )
}

export default App
