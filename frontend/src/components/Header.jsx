import React from 'react';
import { Bot, Bell } from 'lucide-react';

const Header = ({ onNotificationClick }) => {
    return (
        <header className="fixed top-0 left-0 right-0 bg-white/80 backdrop-blur-md border-b border-slate-200 z-50 h-16">
            <div className="max-w-7xl mx-auto px-4 h-full flex items-center justify-between">
                <div className="flex items-center space-x-2">
                    <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-200">
                        <Bot className="w-6 h-6 text-white" />
                    </div>
                    <div>
                        <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-violet-600">
                            AI Learning
                        </h1>
                        <p className="text-xs text-slate-500 font-medium">Platform</p>
                    </div>
                </div>

                <button
                    onClick={onNotificationClick}
                    className="p-2 hover:bg-slate-100 rounded-full relative transition-colors"
                >
                    <Bell className="w-5 h-5 text-slate-600" />
                    <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full border-2 border-white"></span>
                </button>
            </div>
        </header>
    );
};

export default Header;
