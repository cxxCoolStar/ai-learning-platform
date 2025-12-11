import React from 'react';
import { Github, PlayCircle, BookOpen, Clock, Star, ExternalLink, Hash } from 'lucide-react';

const ResourceCard = ({ resource }) => {
    const getIcon = (type) => {
        switch (type) {
            case 'Code': return Github;
            case 'Video': return PlayCircle;
            default: return BookOpen;
        }
    };

    const Icon = getIcon(resource.type);

    return (
        <div className="bg-white rounded-xl border border-slate-200 p-5 hover:shadow-lg hover:border-indigo-200 transition-all duration-300 group">
            <div className="flex justify-between items-start mb-4">
                <div className="flex items-center space-x-3">
                    <div className={`p-2.5 rounded-lg ${resource.type === 'Code' ? 'bg-slate-100 text-slate-700' :
                            resource.type === 'Video' ? 'bg-red-50 text-red-600' :
                                'bg-blue-50 text-blue-600'
                        }`}>
                        <Icon className="w-5 h-5" />
                    </div>
                    <div>
                        <h3 className="font-semibold text-slate-900 group-hover:text-indigo-600 transition-colors line-clamp-1">
                            {resource.title}
                        </h3>
                        <div className="flex items-center space-x-2 text-xs text-slate-500 mt-1">
                            <span>{resource.author || 'Unknown'}</span>
                            <span>•</span>
                            <span className="flex items-center">
                                <Clock className="w-3 h-3 mr-1" />
                                {resource.published_at ? new Date(resource.published_at).toLocaleDateString() : 'Recent'}
                            </span>
                        </div>
                    </div>
                </div>

                {/* Mock Logic for 'New' badge */}
                <span className="px-2 py-1 bg-green-50 text-green-700 text-xs font-medium rounded-full">
                    New
                </span>
            </div>

            <p className="text-slate-600 text-sm mb-4 line-clamp-2 h-10">
                {resource.summary || 'No summary available.'}
            </p>

            <div className="flex flex-wrap gap-2 mb-4 h-16 overflow-hidden">
                {resource.concepts?.slice(0, 3).map((tag, i) => (
                    <span key={i} className="inline-flex items-center px-2 py-1 bg-slate-50 border border-slate-200 rounded-md text-xs font-medium text-slate-600">
                        <Hash className="w-3 h-3 mr-1 text-slate-400" />
                        {tag}
                    </span>
                ))}
                {resource.tech_stack?.slice(0, 3).map((tag, i) => (
                    <span key={'t' + i} className="inline-flex items-center px-2 py-1 bg-indigo-50 border border-indigo-100 rounded-md text-xs font-medium text-indigo-600">
                        {tag}
                    </span>
                ))}
            </div>

            <div className="flex items-center justify-between pt-4 border-t border-slate-100">
                <div className="flex items-center space-x-4 text-sm text-slate-500">
                    <button className="flex items-center hover:text-yellow-500 transition-colors">
                        <Star className="w-4 h-4 mr-1" />
                        <span>1.2k</span>
                    </button>
                </div>

                <a
                    href={resource.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center text-sm font-medium text-indigo-600 hover:text-indigo-700 transition-colors"
                >
                    View Resource
                    <ExternalLink className="w-4 h-4 ml-1" />
                </a>
            </div>
        </div>
    );
};

export default ResourceCard;
