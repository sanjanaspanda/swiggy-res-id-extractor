import { motion } from 'framer-motion';
import { Star, MapPin, ExternalLink, Share2, Heart, Receipt } from 'lucide-react';
import OfferChips from './OfferChips';
import PromoList from './PromoList';

const RestaurantCard = ({ data }) => {
    const { name, location, rating, total_ratings, promo_codes, items_99, url, dineout_only, offer_items_raw } = data;
    const ratingValue = parseFloat(rating);
    const isHighRating = ratingValue >= 4.0;

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full glass-card rounded-2xl overflow-hidden mb-6 border border-base-content/5 hover:border-swiggy-orange/30 transition-all shadow-sm hover:shadow-md"
        >
            {/* Unified Header */}
            <div className="p-6 bg-base-100 flex flex-col md:flex-row gap-6 items-start md:items-center justify-between border-b border-base-200/50">
                {/* Identity */}
                <div className="flex items-center gap-4 flex-1">
                    <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-swiggy-orange to-swiggy-lightOrange text-white flex items-center justify-center text-2xl font-display font-bold shadow-lg shadow-swiggy-orange/10 shrink-0">
                        {name.charAt(0)}
                    </div>
                    <div>
                        <h2 className="text-xl md:text-2xl font-bold font-display leading-tight flex items-center gap-2">
                            {name}
                            {dineout_only && <span className="badge badge-warning gap-1 text-xs font-bold">🍽️ Dineout Only</span>}
                        </h2>
                        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-base-content/60 mt-1">
                            <div className="flex items-center gap-1 text-sm">
                                <MapPin size={14} />
                                <span className="font-medium">{location}</span>
                            </div>
                            <div className="flex items-center gap-1">
                                <div className={`badge badge-sm ${isHighRating ? 'bg-accents-green border-accents-green text-white' : 'bg-yellow-400 border-yellow-400 text-black'} font-bold gap-1`}>
                                    <Star size={10} fill="currentColor" />
                                    {rating}
                                </div>
                                <span className="text-xs font-medium">({total_ratings})</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 self-end md:self-center">
                    <div className="flex gap-1 mr-2">
                        <button className="btn btn-circle btn-ghost btn-sm text-base-content/40 hover:text-error hover:bg-error/10" title="Save">
                            <Heart size={18} />
                        </button>
                        <button className="btn btn-circle btn-ghost btn-sm text-base-content/40 hover:text-primary hover:bg-primary/10" title="Share">
                            <Share2 size={18} />
                        </button>
                    </div>
                    <a
                        href={url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn btn-sm md:btn-md btn-outline border-base-content/20 hover:border-swiggy-orange hover:bg-swiggy-orange hover:text-white gap-2 rounded-xl transition-all font-bold"
                    >
                        View <ExternalLink size={16} />
                    </a>
                </div>
            </div>

            {/* Content Body - Full Width */}
            <div className="p-6 bg-base-50/30 flex flex-col gap-6">

                {/* 1. Offers Section (Full Width) */}
                {(offer_items_raw || (items_99 && items_99.length > 0)) && (
                    <div className="w-full">
                        {/* Dynamic Offer Items Chips */}
                        {offer_items_raw && Object.entries(offer_items_raw).length > 0 ? (
                            Object.entries(offer_items_raw).map(([category, items], idx) => {
                                const colors = ['badge-primary badge-outline', 'badge-secondary badge-outline', 'badge-accent badge-outline', 'badge-neutral badge-outline'];
                                const colorClass = colors[idx % colors.length];
                                return <OfferChips key={category} title={category} items={items} colorClass={colorClass} />;
                            })
                        ) : (
                            items_99 && items_99.length > 0 && <OfferChips title={
                                promo_codes?.find(code => code.split("|")[0].toLowerCase().includes("items at"))?.split("|")[0] || "Items at ₹99"
                            } items={items_99} colorClass="badge-secondary badge-outline" />
                        )}

                        {(!offer_items_raw && (!items_99 || items_99.length === 0)) && (
                            <div className="text-sm opacity-50 italic">No special offers available.</div>
                        )}
                    </div>
                )}

                {/* 2. Promo Codes (If exists) */}
                {promo_codes && promo_codes.length > 0 && (
                    <div className="border-t border-base-200/50 pt-4">
                        <h3 className="text-sm font-bold flex items-center gap-2 mb-3 text-base-content/70 uppercase tracking-wide">
                            <Receipt size={14} />
                            <span>Promo Codes</span>
                        </h3>
                        <PromoList promos={promo_codes} />
                    </div>
                )}
            </div>
        </motion.div>
    );
};

export default RestaurantCard;
