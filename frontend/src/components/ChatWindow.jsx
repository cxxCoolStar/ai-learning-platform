import React, { useState, useRef, useEffect } from 'react';
import { Bot, X, Send, Maximize2, Minimize2, Loader2, Sparkles, MessageSquare } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { sendChatMessageStream } from '../api';

const ChatWindow = ({ isOpen: externalIsOpen, initialMessage, initialQuestions, onClose }) => {
    // Internal state for standalone usage, but controlled by props if provided
    const [internalIsOpen, setInternalIsOpen] = useState(false);
    
    // Determine effective open state
    const isOpen = externalIsOpen !== undefined ? externalIsOpen : internalIsOpen;
    
    const [messages, setMessages] = useState([
        { role: 'assistant', content: '你好！我是AI助手。我可以帮你查找资源或回答关于AI的问题。试试问我"如何使用LangChain？"' }
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const scrollRef = useRef(null);

    const [suggestedQuestions, setSuggestedQuestions] = useState([
        '如何使用LangChain？',
        '推荐AI开源项目',
        'RAG技术是什么？',
        'Agent如何工作？'
    ]);

    // Handle initial props changes (e.g. from "Add to Chat" button)
    useEffect(() => {
        if (initialMessage) {
            setInput(initialMessage);
        }
        if (initialQuestions && initialQuestions.length > 0) {
            setSuggestedQuestions(initialQuestions);
        }
    }, [initialMessage, initialQuestions]);

    const handleClose = () => {
        if (onClose) {
            onClose();
        } else {
            setInternalIsOpen(false);
        }
    };

    const handleOpen = () => {
        setInternalIsOpen(true);
    };

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim()) return;

        const userMsg = input;
        setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
        setInput('');
        setLoading(true);

        try {
            const history = messages.map(m => ({ role: m.role, content: m.content }));
            
            // Placeholder for new assistant message
            setMessages(prev => [...prev, { role: 'assistant', content: '' }]);
            
            let accumulatedContent = '';

            await sendChatMessageStream(userMsg, history, (data) => {
                if (data.type === 'token') {
                    accumulatedContent += data.content;
                    setMessages(prev => {
                        const newMsgs = [...prev];
                        // Update the last message
                        newMsgs[newMsgs.length - 1] = { 
                            role: 'assistant', 
                            content: accumulatedContent 
                        };
                        return newMsgs;
                    });
                } else if (data.type === 'suggestions') {
                    setSuggestedQuestions(data.content);
                }
            });
            
        } catch (error) {
            console.error("Chat Error:", error);
            setMessages(prev => {
                const newMsgs = [...prev];
                // If the last message was the empty placeholder, update it with error
                if (newMsgs[newMsgs.length - 1].role === 'assistant' && newMsgs[newMsgs.length - 1].content === '') {
                     newMsgs[newMsgs.length - 1] = { role: 'assistant', content: '抱歉，遇到了一些问题，请重试。' };
                } else {
                     // Otherwise append error
                     newMsgs.push({ role: 'assistant', content: '抱歉，遇到了一些问题，请重试。' });
                }
                return newMsgs;
            });
        } finally {
            setLoading(false);
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    // 点击推荐问题
    const handleQuestionClick = (question) => {
        setInput(question);
    };

    return (
        <>
            {/* Floating Button - Only show if not controlled externally */}
            {externalIsOpen === undefined && (
                <button
                    onClick={handleOpen}
                    className={`fixed bottom-8 right-8 w-16 h-16 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-full shadow-2xl hover:shadow-3xl hover:scale-110 transition-all flex items-center justify-center group z-40 ${isOpen ? 'scale-0 opacity-0' : 'scale-100 opacity-100'
                        }`}
                >
                    <MessageSquare className="w-7 h-7 group-hover:scale-110 transition-transform" />
                    <span className="absolute -top-12 right-0 bg-slate-800 text-white text-sm px-3 py-2 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                        AI助手搜索
                    </span>
                </button>
            )}

            {/* Chat Window */}
            <div
                className={`fixed bottom-8 right-8 w-96 bg-white rounded-2xl shadow-2xl border border-slate-200 flex flex-col transition-all duration-300 z-50 overflow-hidden ${isOpen ? 'opacity-100 translate-y-0 pointer-events-auto' : 'opacity-0 translate-y-10 pointer-events-none'
                    }`}
                style={{ height: '600px', maxHeight: 'calc(100vh - 4rem)' }}
            >
                {/* Header */}
                <div className="p-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white flex justify-between items-center">
                    <div className="flex items-center space-x-2">
                        <div className="w-8 h-8 bg-white/20 backdrop-blur rounded-lg flex items-center justify-center">
                            <Bot className="w-5 h-5 text-white" />
                        </div>
                        <div>
                            <h3 className="font-semibold text-sm">AI 助手</h3>
                            <p className="text-xs text-indigo-200 flex items-center">
                                <span className="w-1.5 h-1.5 bg-green-400 rounded-full mr-1 animate-pulse"></span>
                                在线
                            </p>
                        </div>
                    </div>
                    <button onClick={handleClose} className="p-1 hover:bg-white/20 rounded-lg transition-colors">
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Messages */}
                <div
                    ref={scrollRef}
                    className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50"
                >
                    {messages.map((msg, idx) => (
                        <div
                            key={idx}
                            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                            <div
                                className={`max-w-[85%] p-3 rounded-2xl text-sm ${msg.role === 'user'
                                        ? 'bg-blue-600 text-white rounded-tr-none'
                                        : 'bg-white border border-slate-200 text-slate-700 rounded-tl-none shadow-sm'
                                    }`}
                            >
                                {msg.role === 'user' ? (
                                    msg.content
                                ) : (
                                    <div className="markdown-content">
                                        <ReactMarkdown 
                                            remarkPlugins={[remarkGfm]}
                                            components={{
                                                a: ({node, ...props}) => <a {...props} className="text-blue-600 hover:underline break-all" target="_blank" rel="noopener noreferrer" />,
                                                ul: ({node, ...props}) => <ul {...props} className="list-disc pl-4 my-2 space-y-1" />,
                                                ol: ({node, ...props}) => <ol {...props} className="list-decimal pl-4 my-2 space-y-1" />,
                                                p: ({node, ...props}) => <p {...props} className="my-1 leading-relaxed" />,
                                                code: ({node, inline, className, children, ...props}) => {
                                                    return inline ? (
                                                        <code className="bg-slate-100 px-1 py-0.5 rounded text-xs font-mono text-slate-800" {...props}>{children}</code>
                                                    ) : (
                                                        <pre className="bg-slate-800 text-slate-100 p-2 rounded-lg my-2 overflow-x-auto text-xs">
                                                            <code {...props}>{children}</code>
                                                        </pre>
                                                    )
                                                }
                                            }}
                                        >
                                            {msg.content}
                                        </ReactMarkdown>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                    {loading && (
                        <div className="flex justify-start">
                            <div className="bg-white border border-slate-200 p-3 rounded-2xl rounded-tl-none shadow-sm flex items-center space-x-2">
                                <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                                <span className="text-sm text-slate-500">思考中...</span>
                            </div>
                        </div>
                    )}
                </div>

                {/* Input Area */}
                <div className="p-4 bg-white border-t border-slate-100">
                    {/* Suggested Questions - 始终显示（除非loading） */}
                    {!loading && suggestedQuestions.length > 0 && (
                        <div className="mb-3 space-y-2">
                            <div className="flex items-center space-x-1 text-xs text-slate-500 mb-2">
                                <Sparkles className="w-3 h-3" />
                                <span>推荐问题</span>
                            </div>
                            <div className="flex flex-wrap gap-2">
                                {suggestedQuestions.map((question, idx) => (
                                    <button
                                        key={idx}
                                        onClick={() => handleQuestionClick(question)}
                                        className="text-xs px-3 py-1.5 bg-blue-50 text-blue-600 rounded-full hover:bg-blue-100 transition-colors border border-blue-200"
                                    >
                                        {question}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}
                    
                    <div className="flex items-center space-x-2 bg-slate-50 p-2 rounded-xl border border-slate-200 focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500 transition-all">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="输入问题..."
                            className="flex-1 bg-transparent border-none focus:ring-0 text-sm text-slate-700 placeholder:text-slate-400"
                        />
                        <button
                            onClick={handleSend}
                            disabled={!input.trim() || loading}
                            className={`p-2 rounded-lg transition-all ${input.trim() && !loading
                                    ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-md'
                                    : 'bg-slate-200 text-slate-400 cursor-not-allowed'
                                }`}
                        >
                            <Send className="w-4 h-4" />
                        </button>
                    </div>
                </div>
            </div>
        </>
    );
};

export default ChatWindow;