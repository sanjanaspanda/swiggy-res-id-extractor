import { useState } from 'react';
import { motion } from 'framer-motion';
import { Search, Loader2, MapPin, Store } from 'lucide-react';

const SearchSection = ({ onSearch, loading, status }) => {
    const [name, setName] = useState('');
    const [location, setLocation] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        onSearch({ name, location });
    };

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4 }}
            className="w-full max-w-xl mx-auto"
        >
            <div className="glass-card rounded-3xl p-8 relative overflow-hidden group">
                {/* Decorative background blob */}
                <div className="absolute -top-20 -right-20 w-40 h-40 bg-swiggy-orange/10 rounded-full blur-3xl group-hover:bg-swiggy-orange/20 transition-all duration-500"></div>

                <form onSubmit={handleSubmit} className="relative z-10 flex flex-col gap-6">

                    <div className="form-control w-full relative">
                        <label className="label pl-1 pb-1">
                            <span className="label-text font-semibold text-base-content/80">Restaurant Name</span>
                        </label>
                        <div className="relative">
                            <Store className="absolute left-4 top-1/2 -translate-y-1/2 text-base-content/40 h-5 w-5" />
                            <input
                                type="text"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                placeholder="e.g. Pizza Hut"
                                className="input input-bordered w-full pl-12 h-14 bg-base-100/50 focus:bg-gray-50 dark:focus:bg-white/10 text-lg transition-all focus:border-swiggy-orange focus:ring-4 focus:ring-swiggy-orange/10 rounded-2xl text-base-content placeholder:text-base-content/40"
                                disabled={loading}
                            />
                        </div>
                    </div>

                    <div className="form-control w-full relative">
                        <label className="label pl-1 pb-1">
                            <span className="label-text font-semibold text-base-content/80">Location</span>
                        </label>
                        <div className="relative">
                            <MapPin className="absolute left-4 top-1/2 -translate-y-1/2 text-base-content/40 h-5 w-5" />
                            <input
                                type="text"
                                value={location}
                                onChange={(e) => setLocation(e.target.value)}
                                placeholder="e.g. Mumbai"
                                className="input input-bordered w-full pl-12 h-14 bg-base-100/50 focus:bg-gray-50 dark:focus:bg-white/10 text-lg transition-all focus:border-swiggy-purple focus:ring-4 focus:ring-swiggy-purple/10 rounded-2xl text-base-content placeholder:text-base-content/40"
                                disabled={loading}
                            />
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={loading || !name || !location}
                        className="btn border-none bg-gradient-to-r from-swiggy-orange to-swiggy-lightOrange hover:brightness-110 text-white w-full h-14 rounded-2xl text-lg font-bold shadow-lg shadow-swiggy-orange/30 mt-2 transform transition-transform active:scale-95 disabled:opacity-70 disabled:scale-100"
                    >
                        {loading ? (
                            <div className="flex items-center gap-2">
                                <Loader2 className="animate-spin" />
                                <span>{status || 'Searching...'}</span>
                            </div>
                        ) : (
                            <div className="flex items-center gap-2">
                                <Search className="w-5 h-5" />
                                <span>Search & Extract</span>
                            </div>
                        )}
                    </button>
                </form>
            </div>
        </motion.div>
    );
};

export default SearchSection;
