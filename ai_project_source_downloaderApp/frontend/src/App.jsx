import { useState } from 'react'

export default function App() {
  const [text, setText] = useState('')

  async function upload() {
    alert('Parser integration placeholder')
  }

  return (
    <div style={{padding:20}}>
      <h1>AI Project Source Downloader</h1>

      <textarea
        rows="20"
        cols="100"
        value={text}
        onChange={(e)=>setText(e.target.value)}
        placeholder="Paste AI generated code here"
      />

      <br /><br />

      <button onClick={upload}>
        Parse & Reconstruct
      </button>
    </div>
  )
}