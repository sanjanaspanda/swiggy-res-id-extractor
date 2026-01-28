import { motion } from 'framer-motion';
import { Utensils, Zap, Truck } from 'lucide-react';

const floatingVariant = {
    animate: {
        y: [0, -10, 0],
        transition: {
            duration: 3,
            repeat: Infinity,
            ease: "easeInOut"
        }
    }
};

const Header = () => {
    return (
        <motion.header
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center relative py-10 px-4 mb-8"
        >
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-full max-w-4xl opacity-10 pointer-events-none">
                {/* Background decoration elements could go here */}
            </div>

            <div className="relative inline-block">
                <motion.div
                    variants={floatingVariant}
                    animate="animate"
                    className="absolute -left-12 -top-4 text-swiggy-orange"
                >
                    <Utensils size={32} />
                </motion.div>

                <h1 className="text-5xl md:text-7xl font-display font-extrabold mb-4 tracking-tight">
                    <span className="text-base-content">Swiggy</span>
                    <span className="text-gradient ml-2">Extractor</span>
                </h1>

                <motion.div
                    variants={floatingVariant}
                    animate="animate"
                    transition={{ delay: 1.5 }}
                    className="absolute -right-12 -bottom-2 text-swiggy-lightPurple"
                >
                    <Truck size={32} />
                </motion.div>
            </div>

            <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3 }}
                className="text-xl text-base-content/70 font-medium max-w-2xl mx-auto mt-4"
            >
                Instantly extract promo codes, ratings, and menu items with a single click.
            </motion.p>
        </motion.header>
    );
};

export default Header;
