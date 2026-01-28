import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, FileText, CheckCircle, XCircle, Loader2, Download, Search, Database } from 'lucide-react';

const BulkUploadSection = () => {
    const [file, setFile] = useState(null);
    const [jobId, setJobId] = useState(null);
    const [items, setItems] = useState([]);
    const [status, setStatus] = useState('idle'); // idle, uploading, processing, completed
    const [progress, setProgress] = useState(0);
    const wsRef = useRef(null);

    const handleFileChange = (e) => {
        if (e.target.files[0]) {
            setFile(e.target.files[0]);
        }
    };

    const handleUpload = async () => {
        if (!file) return;

        setStatus('uploading');
        const formData = new FormData();
        formData.append('file', file);

        try {
            const res = await axios.post('http://localhost:8000/api/v1/bulk/upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });

            setJobId(res.data.job_id);
            setItems(res.data.items);
            setStatus('processing');
            connectWebSocket(res.data.job_id);
        } catch (err) {
            console.error(err);
            setStatus('error');
            alert('Upload failed: ' + (err.response?.data?.detail || err.message));
        }
    };

    const connectWebSocket = (id) => {
        const ws = new WebSocket(`ws://localhost:8000/api/v1/bulk/ws/${id}`);
        wsRef.current = ws;

        ws.onmessage = (event) => {
            const msg = JSON.parse(event.data);

            if (msg.type === 'update') {
                setItems(prev => prev.map(item =>
                    item.id === msg.data.id ? { ...item, ...msg.data } : item
                ));
            } else if (msg.type === 'complete') {
                setStatus('completed');
                ws.close();
            }
        };

        ws.onclose = () => {
            if (status === 'processing') {
                // Maybe reconnect or handled by complete type
            }
        };
    };

    useEffect(() => {
        // Calculate progress
        if (items.length === 0) return;
        const completed = items.filter(i => i.status === 'Completed' || i.status === 'Failed' || i.status === 'Error' || i.status === 'Not Found').length;
        setProgress(Math.round((completed / items.length) * 100));
    }, [items]);

    useEffect(() => {
        return () => {
            if (wsRef.current) wsRef.current.close();
        };
    }, []);

    const handleDownload = async () => {
        try {
            window.open(`http://localhost:8000/api/v1/bulk/download/${jobId}`, '_blank');
        } catch (err) {
            console.error(err);
        }
    };

    const getStatusIcon = (status) => {
        switch (status) {
            case 'Completed': return <CheckCircle className="text-success" size={18} />;
            case 'Failed':
            case 'Error':
            case 'Not Found': return <XCircle className="text-error" size={18} />;
            case 'Processing':
            case 'Searching':
            case 'Extracting': return <Loader2 className="animate-spin text-swiggy-orange" size={18} />;
            default: return <div className="w-4 h-4 rounded-full border-2 border-base-content/20" />;
        }
    };

    return (
        <div className="w-full max-w-4xl mx-auto">
            <div className="glass-card p-8 rounded-3xl mb-8 border-t-4 border-t-swiggy-purple">
                <h2 className="text-2xl font-display font-bold mb-6 flex items-center gap-2">
                    <Database className="text-swiggy-purple" />
                    Bulk Extraction
                </h2>

                {status === 'idle' || status === 'error' ? (
                    <div className="flex flex-col items-center justify-center p-8 border-2 border-dashed border-base-content/20 rounded-2xl bg-base-100/50 hover:bg-base-100/80 transition-all">
                        <FileText size={48} className="text-base-content/30 mb-4" />
                        <input
                            type="file"
                            accept=".csv"
                            onChange={handleFileChange}
                            className="file-input file-input-bordered file-input-primary w-full max-w-xs mb-4"
                        />
                        <p className="text-sm text-base-content/60 mb-4">
                            Upload a CSV with <strong>Restaurant Name</strong> and <strong>Location</strong> headers.
                        </p>
                        <button
                            onClick={handleUpload}
                            disabled={!file}
                            className="btn btn-primary bg-swiggy-purple hover:bg-swiggy-purple/90 border-none px-8 rounded-xl"
                        >
                            <Upload size={18} className="mr-2" /> Start Processing
                        </button>
                    </div>
                ) : (
                    <div>
                        <div className="flex justify-between items-end mb-2">
                            <span className="font-bold text-lg">{progress}% Completed</span>
                            {status === 'completed' && (
                                <div className="flex gap-2">
                                    <button
                                        onClick={() => {
                                            setStatus('idle');
                                            setFile(null);
                                            setItems([]);
                                            setProgress(0);
                                            setJobId(null);
                                        }}
                                        className="btn btn-outline gap-2"
                                    >
                                        <Upload size={16} /> Upload Another
                                    </button>
                                    <button onClick={handleDownload} className="btn btn-success gap-2 text-white animate-bounce-short">
                                        <Download size={16} /> Download CSV
                                    </button>
                                </div>
                            )}
                        </div>
                        <progress className={`progress w-full h-3 mb-8 ${status === 'completed' ? 'progress-success' : 'progress-primary'}`} value={progress} max="100"></progress>

                        <div className="bg-base-100/50 rounded-2xl border border-base-content/5 overflow-hidden max-h-[500px] overflow-y-auto custom-scrollbar">
                            <table className="table w-full">
                                <thead className="bg-base-200/50 sticky top-0 z-10 backdrop-blur-md">
                                    <tr>
                                        <th>Status</th>
                                        <th>Restaurant</th>
                                        <th>Data</th>
                                        <th>Details</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <AnimatePresence>
                                        {items.map((item) => (
                                            <motion.tr
                                                key={item.id}
                                                initial={{ opacity: 0 }}
                                                animate={{ opacity: 1 }}
                                                layout
                                                className="hover:bg-base-100/80 transition-colors"
                                            >
                                                <td>
                                                    <div className="tooltip" data-tip={item.status}>
                                                        {getStatusIcon(item.status)}
                                                    </div>
                                                </td>
                                                <td className="font-medium">
                                                    <div>{item.name}</div>
                                                    <div className="text-xs text-base-content/50">{item.location}</div>
                                                </td>
                                                <td className="text-xs">
                                                    {item.status === 'Completed' ? (
                                                        <div className="flex flex-col gap-1">
                                                            <div className="font-bold flex items-center gap-1">⭐ {item.rating || 'N/A'} <span className="text-base-content/40 font-normal">({item.total_ratings || 0})</span></div>
                                                            <div className="truncate max-w-[150px]" title={item.promo_codes}>{item.promo_codes ? 'Active Promos' : 'No Promos'}</div>
                                                        </div>
                                                    ) : (
                                                        <span className="opacity-30">-</span>
                                                    )}
                                                </td>
                                                <td className="text-xs font-mono">
                                                    {item.status === 'Searching' && <span className="text-info flex items-center gap-1"><Search size={12} /> Searching...</span>}
                                                    {item.status === 'Extracting' && <span className="text-warning flex items-center gap-1"><Loader2 size={12} className="animate-spin" /> Extracting...</span>}
                                                    {item.status === 'Completed' && (
                                                        <div className="flex flex-col">
                                                            <span className="text-success">Done</span>
                                                            {item.dineout_only && <span className="text-[10px] bg-yellow-100 text-yellow-800 px-1 rounded w-fit">Dineout Only</span>}
                                                            <a href={item.swiggy_url} target="_blank" className="hover:underline text-blue-500">View Link</a>
                                                        </div>
                                                    )}
                                                    {(item.status === 'Failed' || item.status === 'Not Found' || item.status === 'Error') && <span className="text-error truncate max-w-[150px] block">{item.error || 'Not Found'}</span>}
                                                </td>
                                            </motion.tr>
                                        ))}
                                    </AnimatePresence>
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default BulkUploadSection;
