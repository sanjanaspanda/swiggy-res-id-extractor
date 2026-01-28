import { Scissors, Copy, Tag, Check } from 'lucide-react';
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const PromoList = ({ promos }) => {
    const [copiedIndex, setCopiedIndex] = useState(null);

    const handleCopy = (code, index) => {
        navigator.clipboard.writeText(code);
        setCopiedIndex(index);
        setTimeout(() => setCopiedIndex(null), 2000);
    };

    if (!promos || promos.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center p-8 text-base-content/40 bg-base-200/50 rounded-xl border border-dashed border-base-300">
                <Tag className="w-8 h-8 mb-2 opacity-50" />
                <span className="text-sm font-medium">No active promo codes</span>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            <h3 className="text-lg font-bold flex items-center gap-2 mb-3">
                <Tag className="text-swiggy-orange" size={20} />
                <span>Available Offers</span>
                <span className="badge badge-outline text-xs font-normal">{promos.length}</span>
            </h3>

            <div className="grid grid-cols-1 gap-3">
                {promos.map((promo, index) => (
                    <motion.div
                        key={index}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.1 }}
                        className="group relative bg-gradient-to-r from-yellow-50 to-orange-50 dark:from-neutral/50 dark:to-neutral/30 border border-orange-100 dark:border-white/5 rounded-lg p-0 overflow-hidden shadow-sm hover:shadow-md transition-shadow"
                    >
                        {/* Coupon Scissor Cut Effect */}
                        <div className="scissors-border absolute bottom-0 left-0 w-full h-[1px] opacity-10"></div>
                        <div className="absolute -left-2 top-1/2 -translate-y-1/2 w-4 h-4 bg-base-100 rounded-full border border-orange-100 dark:border-white/5"></div>
                        <div className="absolute -right-2 top-1/2 -translate-y-1/2 w-4 h-4 bg-base-100 rounded-full border border-orange-100 dark:border-white/5"></div>

                        <div className="flex items-center justify-between p-3 pl-6 pr-4">
                            <div className="flex items-center gap-3 overflow-hidden">
                                <div className="p-2 bg-white dark:bg-white/10 rounded-full text-swiggy-orange shrink-0">
                                    <Scissors size={14} className="transform -rotate-90" />
                                </div>
                                <div className="flex flex-col min-w-0">
                                    <span className="font-bold text-sm md:text-base truncate pr-2" title={promo}>
                                        {promo}
                                    </span>
                                    <span className="text-[10px] uppercase tracking-wider text-base-content/60 font-bold">Coupon Code</span>
                                </div>
                            </div>

                            <button
                                onClick={() => handleCopy(promo, index)}
                                className="btn btn-sm btn-ghost btn-circle bg-white/80 dark:bg-black/20 hover:bg-swiggy-orange hover:text-white transition-colors"
                            >
                                <AnimatePresence mode='wait'>
                                    {copiedIndex === index ? (
                                        <motion.div
                                            key="check"
                                            initial={{ scale: 0 }}
                                            animate={{ scale: 1 }}
                                            exit={{ scale: 0 }}
                                        >
                                            <Check size={16} />
                                        </motion.div>
                                    ) : (
                                        <motion.div
                                            key="copy"
                                            initial={{ scale: 0 }}
                                            animate={{ scale: 1 }}
                                            exit={{ scale: 0 }}
                                        >
                                            <Copy size={16} />
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </button>
                        </div>
                    </motion.div>
                ))}
            </div>
        </div>
    );
};

export default PromoList;
