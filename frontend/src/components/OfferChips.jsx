import { ShoppingBag } from 'lucide-react';

const OfferChips = ({ title, items, colorClass = "badge-neutral" }) => {
    if (!items || items.length === 0) return null;

    return (
        <div className="mb-6 last:mb-0">
            <h3 className="text-sm font-bold flex items-center gap-2 mb-2 px-1 text-base-content/70 uppercase tracking-wide">
                <ShoppingBag size={14} />
                <span>{title}</span>
                <span className="text-xs opacity-50">({items.length})</span>
            </h3>

            <div className="flex flex-wrap gap-2">
                {items.map((item, index) => (
                    <span
                        key={index}
                        className={`badge ${colorClass} badge-lg h-auto py-2 px-3 text-sm font-medium text-center leading-tight`}
                        title={item}
                    >
                        {item}
                    </span>
                ))}
            </div>
        </div>
    );
};

export default OfferChips;
