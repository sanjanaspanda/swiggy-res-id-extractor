import { useState, useEffect } from 'react';
import { Moon, Sun } from 'lucide-react';

const ThemeToggle = () => {
    const [theme, setTheme] = useState(localStorage.getItem('theme') || 'swiggyTheme');

    useEffect(() => {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);

        // Add specific class for dark mode for non-daisyui tailoring if needed
        if (theme === 'swiggyDark') {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
    }, [theme]);

    const toggleTheme = () => {
        setTheme(theme === 'swiggyTheme' ? 'swiggyDark' : 'swiggyTheme');
    };

    return (
        <button
            onClick={toggleTheme}
            className="fixed top-6 right-6 p-3 rounded-full bg-base-100 shadow-lg border border-base-200 z-50 text-base-content hover:scale-110 transition-transform"
            aria-label="Toggle Theme"
        >
            {theme === 'swiggyTheme' ? <Moon size={20} /> : <Sun size={20} />}
        </button>
    );
};

export default ThemeToggle;
