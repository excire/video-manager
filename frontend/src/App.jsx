import { useState, useEffect } from 'react';
import axios from 'axios';
import { Play, Star, Tag, Shuffle, Plus, List as ListIcon } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

function App() {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [videoDir, setVideoDir] = useState('');
  const [savingVideoDir, setSavingVideoDir] = useState(false);

  useEffect(() => {
    fetchVideos();
    fetchVideoDir();
  }, []);

  const fetchVideos = async () => {
    try {
      const res = await axios.get(`${API_BASE}/videos`);
      setVideos(res.data);
      setLoading(false);
    } catch (err) {
      console.error(err);
      setLoading(false);
    }
  };

  const handleScan = async () => {
    await axios.post(`${API_BASE}/scan`);
    alert('Scan started in background');
  };

  const fetchVideoDir = async () => {
    try {
      const res = await axios.get(`${API_BASE}/settings/video-dir`);
      setVideoDir(res.data.video_dir || '');
    } catch (err) {
      console.error(err);
    }
  };

  const handleUpdateVideoDir = async () => {
    if (!videoDir.trim()) {
      alert('Video directory is required');
      return;
    }
    setSavingVideoDir(true);
    try {
      const res = await axios.put(`${API_BASE}/settings/video-dir`, {
        video_dir: videoDir.trim(),
      });
      setVideoDir(res.data.video_dir || videoDir.trim());
      alert('Video directory updated');
    } catch (err) {
      alert('Failed to update video directory');
      console.error(err);
    } finally {
      setSavingVideoDir(false);
    }
  };

  const handleRandom = async () => {
    try {
      const res = await axios.get(`${API_BASE}/videos/random`);
      alert(`Random Video: ${res.data.title}`);
    } catch (err) {
      alert('No videos found');
    }
  };

  return (
    <div className="min-h-screen p-8">
      <header className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-red-500">LocalTube</h1>
        <div className="flex gap-4">
          <button onClick={handleRandom} className="flex items-center gap-2 bg-purple-600 px-4 py-2 rounded hover:bg-purple-700">
            <Shuffle size={20} /> Random
          </button>
          <button onClick={handleScan} className="flex items-center gap-2 bg-blue-600 px-4 py-2 rounded hover:bg-blue-700">
            Scan Videos
          </button>
        </div>
      </header>

      <section className="bg-gray-900 rounded-lg p-4 mb-8">
        <h2 className="text-lg font-semibold mb-3">Video Directory</h2>
        <div className="flex flex-col md:flex-row gap-3 md:items-center">
          <input
            type="text"
            className="flex-1 bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm"
            placeholder="e.g. /videos"
            value={videoDir}
            onChange={(e) => setVideoDir(e.target.value)}
          />
          <button
            onClick={handleUpdateVideoDir}
            className="flex items-center gap-2 bg-green-600 px-4 py-2 rounded hover:bg-green-700 disabled:opacity-60"
            disabled={savingVideoDir}
          >
            {savingVideoDir ? 'Saving...' : 'Save'}
          </button>
        </div>
      </section>

      {loading ? (
        <p>Loading...</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {videos.map(video => (
            <div key={video.id} className="bg-gray-800 rounded-lg overflow-hidden shadow-lg hover:scale-105 transition-transform">
              <div className="aspect-video bg-black relative group">
                {video.thumbnail_path ? (
                  <img src={`${API_BASE}/static/thumbnails/${video.id}`} alt={video.title} className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-gray-500">No Thumb</div>
                )}
                <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 bg-black/40 transition-opacity">
                  <Play size={48} className="text-white" />
                </div>
              </div>
              <div className="p-4">
                <h2 className="font-semibold truncate mb-2">{video.title}</h2>
                <div className="flex justify-between items-center text-sm text-gray-400">
                  <div className="flex items-center gap-1">
                    <Star size={16} className="text-yellow-500" />
                    {video.rating}/10
                  </div>
                  <div className="flex gap-2">
                    {video.tags?.slice(0, 2).map(tag => (
                      <span key={tag.id} className="bg-gray-700 px-2 py-0.5 rounded text-xs flex items-center gap-1">
                        <Tag size={10} /> {tag.name}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default App;
