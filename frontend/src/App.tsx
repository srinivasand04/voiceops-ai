import { useState } from "react";

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState("");
  const [uploading, setUploading] = useState(false);

  const handleFileChange = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const selectedFile = event.target.files?.[0];

    if (!selectedFile) {
      setFile(null);
      return;
    }

    setFile(selectedFile);
    setMessage("");
  };

  const uploadAudio = async () => {
    if (!file) {
      setMessage("Please select an audio file first.");
      return;
    }

    setUploading(true);
    setMessage("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch("/api/calls/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Upload failed");
      }

      const data = await response.json();

      setMessage(
        `Audio uploaded successfully. Call ID: ${data.id}`
      );

      setFile(null);
    } catch (error) {
      console.error(error);
      setMessage("Failed to upload audio.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <h1>VoiceOps AI</h1>

      <h2>Upload Customer Call</h2>

      <input
        type="file"
        accept=".wav,.mp3,.mpeg,audio/*"
        onChange={handleFileChange}
      />

      {file && (
        <p>
          Selected file: <strong>{file.name}</strong>
        </p>
      )}

      <button
        onClick={uploadAudio}
        disabled={uploading}
      >
        {uploading ? "Uploading..." : "Upload Audio"}
      </button>

      {message && <p>{message}</p>}
    </div>
  );
}

export default App;
