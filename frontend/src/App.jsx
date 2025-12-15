import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, Bell, Github, FileText, Video, MessageSquare, Plus, Filter, Mail, Star, ExternalLink, Calendar, Tag, BookOpen, TrendingUp, Loader2, ThumbsUp, ThumbsDown } from 'lucide-react';
import { fetchResources, fetchResourceStats, submitFeedback, generateQuestions } from './api';
import ChatWindow from './components/ChatWindow';

const App = () => {
    const [activeTab, setActiveTab] = useState('all');
    const [searchQuery, setSearchQuery] = useState('');
    const [showNotificationSettings, setShowNotificationSettings] = useState(false);

    // Feedback Modal State
    const [feedbackModal, setFeedbackModal] = useState({ isOpen: false, resourceId: null, voteType: null });
    const [feedbackReason, setFeedbackReason] = useState('');

    // Chat State for "Add to AI Chat"
    const [chatState, setChatState] = useState({
        isOpen: false,
        initialMessage: null,
        initialQuestions: []
    });

    const handleAddToChat = async (e, resource) => {
        e.stopPropagation();
        // Open chat immediately with loading state
        setChatState({
            isOpen: true,
            initialMessage: `我想了解更多关于 "${resource.title}" 的信息。`,
            initialQuestions: [] // Clear previous suggestions
        });

        try {
            // Generate questions in background
            const questions = await generateQuestions(resource.id, resource.title, resource.description);
            // Update chat with generated questions
            setChatState(prev => ({
                ...prev,
                initialQuestions: questions
            }));
        } catch (error) {
            console.error("Failed to generate questions", error);
        }
    };

    const handleFeedbackClick = (e, resourceId, voteType) => {
        e.stopPropagation();
        setFeedbackModal({ isOpen: true, resourceId, voteType });
    };

    const handleFeedbackSubmit = async () => {
        if (!feedbackModal.resourceId) return;

        try {
            await submitFeedback(feedbackModal.resourceId, feedbackModal.voteType, feedbackReason);
            // Optionally show success toast
            setFeedbackModal({ isOpen: false, resourceId: null, voteType: null });
            setFeedbackReason('');
        } catch (error) {
            console.error("Feedback failed", error);
        }
    };

    // Fetch Stats
    const { data: stats = { all: 0, code: 0, article: 0, video: 0, forum: 0 } } = useQuery({
        queryKey: ['resourceStats'],
        queryFn: fetchResourceStats
    });

    const categories = [
        { id: 'all', name: '全部资源', icon: BookOpen, count: stats.all },
        { id: 'code', name: '代码仓库', icon: Github, count: stats.code },
        { id: 'article', name: '技术文章', icon: FileText, count: stats.article },
        { id: 'video', name: '视频教程', icon: Video, count: stats.video },
        { id: 'forum', name: '社区讨论', icon: MessageSquare, count: stats.forum }
    ];

    const tabToApiType = {
        'all': undefined,
        'code': 'Code',
        'article': 'Article',
        'video': 'Video',
        'forum': 'Forum'
    };

    const { data: backendResources = [], isLoading } = useQuery({
        queryKey: ['resources', activeTab, searchQuery],
        queryFn: () => fetchResources({
            type: tabToApiType[activeTab],
            search: searchQuery || undefined
        }),
    });

    const displayResources = backendResources.map(r => ({
        id: r.id,
        type: r.type ? r.type.toLowerCase() : 'article',
        title: r.title,
        url: r.url,
        description: r.summary,
        recommended_reason: r.recommended_reason, // Map this field
        author: r.author, // Map author
        tags: [...(r.concepts || []), ...(r.tech_stack || [])],
        stars: null,
        updatedAt: r.published_at ? new Date(r.published_at).toLocaleDateString() : 'Recently',
        isNew: false
    }));

    const getTypeIcon = (type) => {
        const icons = {
            code: Github,
            article: FileText,
            video: Video,
            forum: MessageSquare
        };
        const Icon = icons[type] || BookOpen;
        return Icon ? <Icon className="w-4 h-4" /> : null;
    };

    return (
        <div className="flex h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 overflow-hidden">
            {/* Main Content Area */}
            <div className="flex-1 flex flex-col min-w-0 transition-all duration-300">
                {/* Header */}
                <header className="bg-white/80 backdrop-blur-lg border-b border-slate-200 sticky top-0 z-20 shrink-0">
                    <div className="max-w-7xl mx-auto px-6 py-4">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center">
                                    <TrendingUp className="w-6 h-6 text-white" />
                                </div>
                                <div>
                                    <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                                        AI学习平台
                                    </h1>
                                    <p className="text-xs text-slate-500">智能资源聚合与推荐</p>
                                </div>
                            </div>

                            <div className="flex items-center gap-3">
                                <button
                                    onClick={() => setShowNotificationSettings(!showNotificationSettings)}
                                    className="relative p-2 hover:bg-slate-100 rounded-lg transition-colors"
                                >
                                    <Bell className="w-5 h-5 text-slate-600" />
                                    <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
                                </button>
                                <button className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg hover:shadow-lg transition-all">
                                    <Plus className="w-4 h-4" />
                                    <span className="text-sm font-medium">添加资源</span>
                                </button>
                            </div>
                        </div>
                    </div>
                </header>

                {/* Scrollable Content */}
                <div className="flex-1 overflow-y-auto scroll-smooth">
                    <div className="max-w-7xl mx-auto px-6 py-8">
                        {/* Search and Filter */}
                        <div className="mb-8">
                            <div className="bg-white rounded-2xl shadow-lg p-6">
                                <div className="flex gap-4 mb-6">
                                    <div className="flex-1 relative">
                                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                                        <input
                                            type="text"
                                            placeholder="搜索资源标题、描述、标签..."
                                            value={searchQuery}
                                            onChange={(e) => setSearchQuery(e.target.value)}
                                            className="w-full pl-12 pr-4 py-3 bg-slate-50 rounded-xl border-2 border-transparent focus:border-blue-500 focus:bg-white outline-none transition-all"
                                        />
                                    </div>
                                    <button className="flex items-center gap-2 px-6 py-3 bg-slate-100 hover:bg-slate-200 rounded-xl transition-colors">
                                        <Filter className="w-4 h-4" />
                                        <span className="font-medium">筛选</span>
                                    </button>
                                </div>

                                {/* Category Tabs */}
                                <div className="flex gap-2 overflow-x-auto pb-2">
                                    {categories.map((cat) => {
                                        const Icon = cat.icon;
                                        const isActive = activeTab === cat.id;
                                        return (
                                            <button
                                                key={cat.id}
                                                onClick={() => setActiveTab(cat.id)}
                                                className={`flex items-center gap-2 px-4 py-2 rounded-lg whitespace-nowrap transition-all ${isActive
                                                    ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg'
                                                    : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                                                    }`}
                                            >
                                                <Icon className="w-4 h-4" />
                                                <span className="font-medium">{cat.name}</span>
                                                <span className={`text-xs px-2 py-0.5 rounded-full ${isActive ? 'bg-white/20' : 'bg-slate-200'
                                                    }`}>
                                                    {cat.count}
                                                </span>
                                            </button>
                                        );
                                    })}
                                </div>
                            </div>
                        </div>

                        {/* Resources Grid */}
                        {isLoading ? (
                            <div className="flex justify-center items-center h-64">
                                <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
                            </div>
                        ) : (
                            <div className="grid gap-6">
                                {displayResources.length > 0 ? (
                                    displayResources.map((resource) => (
                                        <div
                                            key={resource.id}
                                            onClick={() => window.open(resource.url, '_blank')}
                                            className="bg-white rounded-2xl shadow-lg hover:shadow-xl transition-all overflow-hidden group cursor-pointer"
                                        >
                                            <div className="p-6">
                                                <div className="flex items-start justify-between mb-4">
                                                    <div className="flex items-start gap-4 flex-1">
                                                        <div className={`p-3 rounded-xl ${resource.type === 'code' ? 'bg-purple-100 text-purple-600' :
                                                            resource.type === 'article' ? 'bg-blue-100 text-blue-600' :
                                                                resource.type === 'video' ? 'bg-red-100 text-red-600' :
                                                                    'bg-green-100 text-green-600'
                                                            }`}>
                                                            {getTypeIcon(resource.type)}
                                                        </div>

                                                        <div className="flex-1">
                                                            <div className="flex items-center gap-2 mb-2">
                                                                <h3 className="text-lg font-bold text-slate-800 group-hover:text-blue-600 transition-colors">
                                                                    {resource.title}
                                                                </h3>
                                                                {resource.isNew && (
                                                                    <span className="px-2 py-0.5 bg-gradient-to-r from-orange-400 to-red-500 text-white text-xs font-bold rounded">
                                                                        NEW
                                                                    </span>
                                                                )}
                                                            </div>

                                                            <p className="text-slate-600 text-sm mb-3 line-clamp-2">
                                                                {resource.description}
                                                            </p>

                                                            {resource.recommended_reason && (
                                                                <div className="mb-3 p-2 bg-indigo-50 border border-indigo-100 rounded-lg text-xs text-indigo-700">
                                                                    {resource.recommended_reason}
                                                                </div>
                                                            )}

                                                            <div className="flex items-center gap-4 text-xs text-slate-500">
                                                                <div className="flex items-center gap-1 font-medium bg-slate-100 px-2 py-0.5 rounded text-slate-700">
                                                                    <span>{resource.author || 'Unknown Author'}</span>
                                                                </div>

                                                                <div className="flex items-center gap-1">
                                                                    <Calendar className="w-3 h-3" />
                                                                    <span>{resource.updatedAt}</span>
                                                                </div>

                                                                {resource.stars && (
                                                                    <div className="flex items-center gap-1">
                                                                        <Star className="w-3 h-3 fill-yellow-400 text-yellow-400" />
                                                                        <span>{resource.stars.toLocaleString()}</span>
                                                                    </div>
                                                                )}

                                                                {resource.readTime && (
                                                                    <span>阅读时间: {resource.readTime}</span>
                                                                )}

                                                                {resource.duration && (
                                                                    <span>时长: {resource.duration}</span>
                                                                )}

                                                                {resource.replies && (
                                                                    <span>{resource.replies} 条回复</span>
                                                                )}
                                                            </div>
                                                        </div>
                                                    </div>

                                                    <div className="flex flex-col gap-2">
                                                        <a
                                                            href={resource.url}
                                                            target="_blank"
                                                            rel="noopener noreferrer"
                                                            onClick={(e) => e.stopPropagation()}
                                                            className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
                                                        >
                                                            <ExternalLink className="w-5 h-5 text-slate-400" />
                                                        </a>
                                                    </div>
                                                </div>

                                                <div className="flex items-center justify-between mt-4">
                                                    <div className="flex items-center gap-2 flex-wrap">
                                                        {resource.tags.map((tag, i) => (
                                                            <span
                                                                key={tag + i}
                                                                onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    // Future: filter by tag
                                                                }}
                                                                className="flex items-center gap-1 px-3 py-1 bg-slate-100 hover:bg-slate-200 rounded-full text-xs font-medium text-slate-700 cursor-pointer transition-colors"
                                                            >
                                                                <Tag className="w-3 h-3" />
                                                                {tag}
                                                            </span>
                                                        ))}
                                                    </div>

                                                    <div className="flex gap-1 shrink-0 ml-2">
                                                        <button
                                                            onClick={(e) => handleAddToChat(e, resource)}
                                                            className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-600 rounded-lg transition-colors font-medium text-xs mr-2"
                                                        >
                                                            <MessageSquare className="w-4 h-4" />
                                                            <span>添加到AI对话</span>
                                                        </button>
                                                        <button
                                                            onClick={(e) => handleFeedbackClick(e, resource.id, 'like')}
                                                            className="p-2 hover:bg-green-50 text-slate-400 hover:text-green-600 rounded-lg transition-colors"
                                                            title="推荐"
                                                        >
                                                            <ThumbsUp className="w-4 h-4" />
                                                        </button>
                                                        <button
                                                            onClick={(e) => handleFeedbackClick(e, resource.id, 'dislike')}
                                                            className="p-2 hover:bg-red-50 text-slate-400 hover:text-red-600 rounded-lg transition-colors"
                                                            title="不感兴趣"
                                                        >
                                                            <ThumbsDown className="w-4 h-4" />
                                                        </button>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    ))
                                ) : (
                                    <div className="col-span-full text-center py-10 text-slate-500">
                                        暂无资源，请尝试其他搜索词或分类。
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Sidebar Container */}
            <div className={`${chatState.isOpen ? 'w-[450px]' : 'w-0'} transition-all duration-300 relative shadow-2xl z-30`}>
                <ChatWindow
                    mode="sidebar"
                    isOpen={chatState.isOpen}
                    initialMessage={chatState.initialMessage}
                    initialQuestions={chatState.initialQuestions}
                    onClose={() => setChatState(prev => ({ ...prev, isOpen: false }))}
                />
            </div>

            {/* Floating Trigger Button (Visible only when sidebar is closed) */}
            <button
                onClick={() => setChatState(prev => ({ ...prev, isOpen: true }))}
                className={`fixed bottom-8 right-8 w-16 h-16 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-full shadow-2xl hover:shadow-3xl hover:scale-110 transition-all flex items-center justify-center group z-40 ${chatState.isOpen ? 'scale-0 opacity-0 pointer-events-none' : 'scale-100 opacity-100'}`}
            >
                <MessageSquare className="w-7 h-7 group-hover:scale-110 transition-transform" />
                <span className="absolute -top-12 right-0 bg-slate-800 text-white text-sm px-3 py-2 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                    AI助手搜索
                </span>
            </button>

            {/* Notification Settings Modal */}
            {showNotificationSettings && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                    <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-bold text-slate-800">邮件订阅设置</h3>
                            <button
                                onClick={() => setShowNotificationSettings(false)}
                                className="p-1 hover:bg-slate-100 rounded-lg"
                            >
                                ✕
                            </button>
                        </div>

                        <div className="space-y-4">
                            <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                                <Mail className="w-5 h-5 text-blue-600" />
                                <div className="flex-1">
                                    <input
                                        type="email"
                                        placeholder="输入QQ邮箱地址"
                                        className="w-full bg-transparent border-none outline-none text-sm"
                                    />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <label className="flex items-center gap-2 cursor-pointer">
                                    <input type="checkbox" className="w-4 h-4" defaultChecked />
                                    <span className="text-sm text-slate-700">代码仓库更新</span>
                                </label>
                                <label className="flex items-center gap-2 cursor-pointer">
                                    <input type="checkbox" className="w-4 h-4" defaultChecked />
                                    <span className="text-sm text-slate-700">技术文章推送</span>
                                </label>
                                <label className="flex items-center gap-2 cursor-pointer">
                                    <input type="checkbox" className="w-4 h-4" defaultChecked />
                                    <span className="text-sm text-slate-700">视频教程更新</span>
                                </label>
                                <label className="flex items-center gap-2 cursor-pointer">
                                    <input type="checkbox" className="w-4 h-4" />
                                    <span className="text-sm text-slate-700">社区热门讨论</span>
                                </label>
                            </div>

                            <div className="flex items-center gap-2 pt-2">
                                <label className="text-sm text-slate-600">推送频率:</label>
                                <select className="flex-1 px-3 py-2 bg-slate-50 rounded-lg text-sm border-none outline-none">
                                    <option>实时推送</option>
                                    <option>每日汇总</option>
                                    <option>每周汇总</option>
                                </select>
                            </div>

                            <button className="w-full py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg font-medium hover:shadow-lg transition-all">
                                保存设置
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Feedback Modal */}
            {feedbackModal.isOpen && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                    <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6" onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-bold text-slate-800">
                                {feedbackModal.voteType === 'like' ? '推荐理由' : '不感兴趣理由'}
                            </h3>
                            <button
                                onClick={() => setFeedbackModal({ isOpen: false, resourceId: null, voteType: null })}
                                className="p-1 hover:bg-slate-100 rounded-lg"
                            >
                                ✕
                            </button>
                        </div>
                        <div className="space-y-4">
                            <textarea
                                value={feedbackReason}
                                onChange={(e) => setFeedbackReason(e.target.value)}
                                placeholder="请告诉我们原因，帮助我们为您提供更精准的推荐..."
                                className="w-full h-32 p-3 bg-slate-50 rounded-xl border border-slate-200 outline-none focus:border-blue-500 transition-all resize-none text-sm"
                            />
                            <div className="flex gap-3">
                                <button
                                    onClick={() => setFeedbackModal({ isOpen: false, resourceId: null, voteType: null })}
                                    className="flex-1 py-2.5 bg-slate-100 text-slate-700 rounded-lg font-medium hover:bg-slate-200 transition-all"
                                >
                                    取消
                                </button>
                                <button
                                    onClick={handleFeedbackSubmit}
                                    className="flex-1 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg font-medium hover:shadow-lg transition-all"
                                >
                                    提交反馈
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default App;
