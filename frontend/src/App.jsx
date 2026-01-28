import { useState } from 'react';
import axios from 'axios';
import { AnimatePresence, motion } from 'framer-motion';
import Header from './components/Header';
import SearchSection from './components/SearchSection';
import BulkUploadSection from './components/BulkUploadSection';
import RestaurantCard from './components/RestaurantCard';
import ThemeToggle from './components/ThemeToggle';
import { Loader2 } from 'lucide-react';

function App() {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [status, setStatus] = useState('');

  const [viewMode, setViewMode] = useState('single'); // 'single' or 'bulk'

  const handleSearch = async ({ name, location }) => {
    setLoading(true);
    setError('');
    setStatus('Searching for restaurant...');

    try {
      // 1. Search
      const searchRes = await axios.post('http://localhost:8000/api/v1/search', {
        name,
        location
      });

      const { url, not_found, dineout_only, error: searchError } = searchRes.data;

      if (not_found) {
        setError(searchError || 'Restaurant not found');
        setStatus('');
        return;
      }

      if (dineout_only) {
        setStatus('Found (Dineout Only). Extraction skipped.');

        const newResult = {
          id: Date.now(),
          name,
          location,
          url,
          rating: 'N/A',
          total_ratings: 'N/A',
          promo_codes: [],
          items_99: [],
          offer_items: {}, // Provide empty dict for generic UI
          dineout_only: true
        };

        setResults(prev => [newResult, ...prev]);
        setLoading(false);
        setStatus('');
        return;
      }

      setStatus('Found URL. Extracting data...');

      // 2. Extract
      const extractData = async (targetUrl) => {
        const res = await axios.post('http://localhost:8000/api/v1/extract', { url: targetUrl });
        return res.data;
      };

      let data = await extractData(url);

      // Check for empty fields (no rating, no promos, no items)
      // Retry ONCE if essentially empty
      if (!data.rating && data.promo_codes.length === 0 && data.items_99.length === 0) {
        setStatus('Data incomplete. Retrying extraction...');
        console.log('Extraction incomplete, retrying...');
        // Optional delay could be added here if backend doesn't handle it
        await new Promise(r => setTimeout(r, 2000));
        data = await extractData(url);
      }

      const newResult = {
        id: Date.now(),
        name,
        location,
        url,
        rating: data.rating,
        total_ratings: data.total_ratings,
        promo_codes: data.promo_codes,
        items_99: data.items_99,
        offer_items: data.offer_items,
        offer_items_raw: data.offer_items,
        dineout_only: dineout_only
      };

      setResults(prev => [newResult, ...prev]);
      setStatus('');

    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || err.message || 'An error occurred');
      setStatus('');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen p-4 md:p-8 relative selection:bg-swiggy-orange selection:text-white">
      <ThemeToggle />

      {/* Dynamic Background Elements */}
      <div className="fixed inset-0 pointer-events-none -z-10 overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-full bg-base-200/50"></div>
        <div className="absolute top-[-10%] right-[-5%] w-[500px] h-[500px] bg-swiggy-orange/5 rounded-full blur-3xl animate-pulse-slow"></div>
        <div className="absolute bottom-[-10%] left-[-5%] w-[500px] h-[500px] bg-swiggy-purple/5 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '2s' }}></div>
      </div>

      <div className="max-w-5xl mx-auto flex flex-col items-center">
        <Header />

        {/* View Toggle */}
        <div className="flex gap-4 mb-8 bg-base-100 p-1 rounded-xl border border-base-content/10 shadow-sm">
          <button
            onClick={() => setViewMode('single')}
            className={`px-6 py-2 rounded-lg text-sm font-bold transition-all ${viewMode === 'single' ? 'bg-swiggy-orange text-white shadow-lg' : 'hover:bg-base-200 text-base-content/60'}`}
          >
            Single Search
          </button>
          <button
            onClick={() => setViewMode('bulk')}
            className={`px-6 py-2 rounded-lg text-sm font-bold transition-all ${viewMode === 'bulk' ? 'bg-swiggy-purple text-white shadow-lg' : 'hover:bg-base-200 text-base-content/60'}`}
          >
            Bulk Upload
          </button>
        </div>

        {viewMode === 'single' ? (
          <>
            <SearchSection onSearch={handleSearch} loading={loading} status={status} />

            <div className="w-full mt-12">
              <AnimatePresence mode='popLayout'>
                {error && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    className="alert alert-error mb-8 shadow-lg max-w-xl mx-auto rounded-2xl border border-red-200"
                  >
                    <span>{error}</span>
                  </motion.div>
                )}

                {results.map((res) => (
                  <RestaurantCard key={res.id} data={res} />
                ))}
              </AnimatePresence>

              {!loading && results.length === 0 && !error && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.5 }}
                  className="text-center mt-20 opacity-40"
                >
                  <div className="text-6xl mb-4 grayscale">🍕</div>
                  <p className="font-display font-medium text-lg">Waiting for your hunger...</p>
                </motion.div>
              )}
            </div>
          </>
        ) : (
          <div className="w-full">
            <BulkUploadSection />
          </div>
        )}
      </div>

      <footer className="mt-20 text-center text-sm font-medium opacity-40 pb-8">
        <p>Made with 🧡 for food lovers</p>
      </footer>
    </div>
  );
}

export default App;
