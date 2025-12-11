import React, { useState } from 'react';
import { Search, Bell, Github, FileText, Video, MessageSquare, Plus, Filter, Mail, Star, ExternalLink, Calendar, Tag, BookOpen, TrendingUp } from 'lucide-react';

const AILearningPlatform = () => {
    const [activeTab, setActiveTab] = useState('all');
    const [searchQuery, setSearchQuery] = useState('');
    const [showNotificationSettings, setShowNotificationSettings] = useState(false);

    const categories = [
        { id: 'all', name: '全部资源', icon: BookOpen, count: 156 },
        { id: 'code', name: '代码仓库', icon: Github, count: 45 },
        { id: 'article', name: '技术文章', icon: FileText, count: 67 },
        { id: 'video', name: '视频教程', icon: Video, count: 32 },
        { id: 'forum', name: '社区讨论', icon: MessageSquare, count: 12 }
    ];

    const resources = [
        {
            id: 1,
            type: 'code',
            title: 'LangChain Python SDK',
            url: 'https://github.com/langchain-ai/langchain',
            description: '用于构建LLM应用的Python框架，支持链式调用、记忆管理和工具集成',
            tags: ['Python', 'LLM', 'Framework'],
            stars: 82500,
            updatedAt: '2小时前',
            isNew: true
        },
        {
            id: 2,
            type: 'article',
            title: 'Building Production-Ready RAG Applications',
            url: 'https://blog.langchain.com/rag-production',
            description: '深入探讨如何构建生产级别的RAG应用，包括性能优化和错误处理',
            tags: ['RAG', 'Production', 'Best Practices'],
            readTime: '12分钟',
            updatedAt: '1天前',
            isNew: true
        },
        {
            id: 3,
            type: 'video',
            title: 'Andrej Karpathy - Let\'s build GPT',
            url: 'https://youtube.com/watch?v=kCc8FmEb1nY',
            description: '从零开始实现GPT模型，理解Transformer架构的每个细节',
            tags: ['Deep Learning', 'GPT', 'Tutorial'],
            duration: '2小时14分',
            updatedAt: '3天前',
            isNew: false
        },
        {
            id: 4,
            type: 'article',
            title: 'Claude Prompt Engineering Guide',
            url: 'https://www.anthropic.com/engineering/prompt-engineering',
            description: 'Anthropic官方提示词工程指南，涵盖最佳实践和高级技巧',
            tags: ['Prompt Engineering', 'Claude', 'Guide'],
            readTime: '8分钟',
            updatedAt: '5天前',
            isNew: false
        },
        {
            id: 5,
            type: 'forum',
            title: 'AI Safety Research Discussion',
            url: 'https://x.com/AnthropicAI',
            description: 'Anthropic团队关于AI安全研究的最新讨论和见解',
            tags: ['AI Safety', 'Research', 'Discussion'],
            replies: 45,
            updatedAt: '6小时前',
            isNew: true
        }
    ];

    const filteredResources = activeTab === 'all'
        ? resources
        : resources.filter(r => r.type === activeTab);

    const getTypeIcon = (type) => {
        const icons = {
            code: Github,
            article: FileText,
            video: Video,
            forum: MessageSquare
        };
        const Icon = icons[type];
        return Icon ? <Icon className="w-4 h-4" /> : null;
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
            {/* Header */}
            <header className="bg-white/80 backdrop-blur-lg border-b border-slate-200 sticky top-0 z-50">
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
                <div className="grid gap-6">
                    {filteredResources.map((resource) => (
                        <div
                            key={resource.id}
                            className="bg-white rounded-2xl shadow-lg hover:shadow-xl transition-all overflow-hidden group"
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

                                            <div className="flex items-center gap-4 text-xs text-slate-500">
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

                                    <a
                                        href={resource.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
                                    >
                                        <ExternalLink className="w-5 h-5 text-slate-400" />
                                    </a>
                                </div>

                                <div className="flex items-center gap-2 flex-wrap">
                                    {resource.tags.map((tag) => (
                                        <span
                                            key={tag}
                                            className="flex items-center gap-1 px-3 py-1 bg-slate-100 hover:bg-slate-200 rounded-full text-xs font-medium text-slate-700 cursor-pointer transition-colors"
                                        >
                                            <Tag className="w-3 h-3" />
                                            {tag}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Chatbot Button */}
                <button className="fixed bottom-8 right-8 w-16 h-16 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-full shadow-2xl hover:shadow-3xl hover:scale-110 transition-all flex items-center justify-center group">
                    <MessageSquare className="w-7 h-7 group-hover:scale-110 transition-transform" />
                    <span className="absolute -top-12 right-0 bg-slate-800 text-white text-sm px-3 py-2 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                        AI助手搜索
                    </span>
                </button>
            </div>
        </div>
    );
};

export default AILearningPlatform;