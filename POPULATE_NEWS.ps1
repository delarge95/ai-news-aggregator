# Script para poblar la base de datos con noticias de ejemplo
# Para AI News Aggregator

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  POBLAR BASE DE DATOS CON NOTICIAS" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# SQL para insertar noticias de ejemplo
$sql = @"
-- Insertar fuentes
INSERT INTO sources (id, name, url, api_type, is_active, created_at, updated_at)
VALUES 
    ('ai-news', 'AI News', 'https://ai-news.example.com', 'api', true, NOW(), NOW()),
    ('tech-crunch', 'TechCrunch AI', 'https://techcrunch.com/ai', 'rss', true, NOW(), NOW()),
    ('mit-news', 'MIT Technology Review', 'https://www.technologyreview.com', 'rss', true, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- Insertar artículos de ejemplo sobre IA
INSERT INTO articles (
    id, title, description, content, url, image_url, 
    published_at, source_id, author, category, 
    sentiment, relevance_score, is_trending,
    created_at, updated_at
)
VALUES 
    (
        gen_random_uuid(),
        'OpenAI Launches GPT-5: The Next Generation of AI Language Models',
        'OpenAI unveils GPT-5, claiming significant improvements in reasoning, context understanding, and multimodal capabilities.',
        'OpenAI has announced the release of GPT-5, its latest and most powerful language model to date. The new model features enhanced reasoning capabilities, better context retention across longer conversations, and improved multimodal understanding combining text, images, and code. CEO Sam Altman stated that GPT-5 represents a major leap forward in AI safety and alignment, with built-in guardrails to prevent misuse. The model will be available through OpenAI''s API with tiered pricing based on usage. Early access partners report significant improvements in complex problem-solving tasks and creative applications.',
        'https://openai.example.com/gpt5-announcement',
        'https://images.unsplash.com/photo-1677442136019-21780ecad995?w=800',
        NOW() - INTERVAL '2 hours',
        'ai-news',
        'Sarah Chen',
        'Machine Learning',
        0.85,
        0.95,
        true,
        NOW(),
        NOW()
    ),
    (
        gen_random_uuid(),
        'Google DeepMind Achieves Breakthrough in Protein Folding with AlphaFold 3',
        'DeepMind''s AlphaFold 3 can now predict protein structures with 99% accuracy, revolutionizing drug discovery.',
        'Google DeepMind has announced AlphaFold 3, the latest iteration of its groundbreaking protein structure prediction system. The new version achieves unprecedented 99% accuracy in predicting how proteins fold, a critical challenge in biology and medicine. This advancement is expected to accelerate drug discovery, enable personalized medicine, and help scientists understand diseases at the molecular level. AlphaFold 3 introduces novel neural network architectures that can model complex protein interactions and dynamics. The research team has made the model openly available to researchers worldwide, continuing DeepMind''s commitment to open science.',
        'https://deepmind.example.com/alphafold3',
        'https://images.unsplash.com/photo-1576086213369-97a306d36557?w=800',
        NOW() - INTERVAL '5 hours',
        'ai-news',
        'Dr. Michael Zhang',
        'Healthcare',
        0.92,
        0.88,
        true,
        NOW(),
        NOW()
    ),
    (
        gen_random_uuid(),
        'AI-Powered Autonomous Vehicles Pass 10 Million Miles Without Incident',
        'Major milestone for self-driving technology as Waymo reports accident-free record across multiple cities.',
        'Waymo, Alphabet''s autonomous vehicle division, has announced a historic milestone: its fleet of self-driving cars has completed over 10 million miles of fully autonomous driving without a single at-fault accident. This achievement demonstrates the maturity and safety of AI-powered transportation systems. The vehicles operate in complex urban environments including San Francisco, Phoenix, and Los Angeles, handling diverse weather conditions, traffic patterns, and road scenarios. Advanced computer vision, sensor fusion, and real-time decision-making algorithms enable the vehicles to navigate safely. Industry experts view this as a turning point for public acceptance of autonomous transportation.',
        'https://waymo.example.com/milestone',
        'https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?w=800',
        NOW() - INTERVAL '8 hours',
        'tech-crunch',
        'Alex Rivera',
        'Autonomous Systems',
        0.78,
        0.82,
        false,
        NOW(),
        NOW()
    ),
    (
        gen_random_uuid(),
        'Microsoft Copilot Integrates Advanced AI Assistants Across Office Suite',
        'Microsoft announces major updates to Copilot, bringing AI assistance to Word, Excel, PowerPoint, and Outlook.',
        'Microsoft has unveiled significant enhancements to its Copilot AI assistant, now deeply integrated across the entire Microsoft 365 suite. The updated Copilot can generate entire presentations from brief prompts, analyze complex Excel datasets with natural language queries, draft emails with context awareness, and assist with document creation in Word. Powered by GPT-4 and Microsoft''s proprietary models, Copilot learns from user preferences and organizational data to provide personalized assistance. Enterprise customers can customize Copilot with company-specific knowledge bases. Early adopters report productivity increases of 30-40% in document creation and data analysis tasks.',
        'https://microsoft.example.com/copilot-update',
        'https://images.unsplash.com/photo-1633356122544-f134324a6cee?w=800',
        NOW() - INTERVAL '12 hours',
        'tech-crunch',
        'Emily Watson',
        'Productivity Tools',
        0.88,
        0.79,
        false,
        NOW(),
        NOW()
    ),
    (
        gen_random_uuid(),
        'AI Detects Early Signs of Alzheimer''s 6 Years Before Clinical Diagnosis',
        'Machine learning model analyzes brain scans to identify Alzheimer''s biomarkers with 95% accuracy.',
        'Researchers at Stanford University have developed an AI system that can detect early signs of Alzheimer''s disease up to six years before traditional clinical diagnosis methods. The deep learning model analyzes brain MRI scans and identifies subtle patterns invisible to human radiologists. In clinical trials involving 5,000 patients, the AI achieved 95% accuracy in predicting which individuals would develop Alzheimer''s within six years. This breakthrough could enable earlier intervention with treatments that slow disease progression. The research team is working with healthcare providers to integrate the AI screening tool into routine brain imaging workflows.',
        'https://stanford.example.com/alzheimers-ai',
        'https://images.unsplash.com/photo-1559757175-5700dde675bc?w=800',
        NOW() - INTERVAL '1 day',
        'mit-news',
        'Dr. Jennifer Park',
        'Healthcare',
        0.82,
        0.91,
        true,
        NOW(),
        NOW()
    ),
    (
        gen_random_uuid(),
        'AI-Generated Art Sells for Record \$5.2 Million at Christie''s Auction',
        'Digital artwork created entirely by artificial intelligence breaks auction records, sparking debate about AI creativity.',
        'A controversial AI-generated artwork has sold for a record-breaking \$5.2 million at Christie''s auction house, reigniting debates about artificial intelligence, creativity, and authorship. The piece, titled "Digital Dreams," was created by a generative AI model trained on thousands of classical and contemporary artworks. The anonymous buyer described the work as "a perfect fusion of algorithmic precision and emotional resonance." Critics argue that AI art lacks the human experience and intentionality that define true artistry, while supporters view it as a new medium expanding the boundaries of creative expression. The sale has prompted discussions about copyright, attribution, and the future role of AI in creative industries.',
        'https://christies.example.com/ai-art-record',
        'https://images.unsplash.com/photo-1547826039-bfc35e0f1ea8?w=800',
        NOW() - INTERVAL '1 day',
        'tech-crunch',
        'Marcus Thompson',
        'Ethics',
        0.65,
        0.77,
        false,
        NOW(),
        NOW()
    ),
    (
        gen_random_uuid(),
        'Climate Scientists Use AI to Predict Extreme Weather Events 30 Days in Advance',
        'New machine learning models improve weather forecasting accuracy, potentially saving thousands of lives.',
        'A collaboration between NOAA and leading AI research labs has resulted in weather prediction models that can forecast extreme events like hurricanes, floods, and heat waves up to 30 days in advance with unprecedented accuracy. The AI system combines satellite imagery, atmospheric data, ocean temperatures, and historical weather patterns to identify precursor signals invisible to traditional forecasting methods. During the 2024 hurricane season, the AI correctly predicted the formation and path of Category 4 Hurricane Delta 28 days before landfall, allowing for early evacuations. Climate scientists believe these AI tools will be crucial for adaptation as climate change increases the frequency of extreme weather events.',
        'https://noaa.example.com/ai-weather-prediction',
        'https://images.unsplash.com/photo-1592210454359-9043f067919b?w=800',
        NOW() - INTERVAL '2 days',
        'mit-news',
        'Dr. Carlos Rodriguez',
        'Climate',
        0.88,
        0.85,
        false,
        NOW(),
        NOW()
    ),
    (
        gen_random_uuid(),
        'OpenAI Introduces Code Interpreter: AI That Writes and Executes Code in Real-Time',
        'ChatGPT''s new code interpreter feature allows users to analyze data, create visualizations, and solve problems through code.',
        'OpenAI has launched Code Interpreter, a powerful new feature for ChatGPT that enables the AI to write and execute Python code in a secure sandbox environment. Users can upload datasets, request analyses, and receive working code with visualizations and insights. The system can handle complex data science tasks, generate interactive charts, solve mathematical problems, and even create simple games or applications. Early users have employed Code Interpreter for financial analysis, scientific data processing, image manipulation, and educational purposes. The feature represents a significant step toward AI systems that can perform multi-step reasoning and tool use to accomplish complex goals.',
        'https://openai.example.com/code-interpreter',
        'https://images.unsplash.com/photo-1461749280684-dccba630e2f6?w=800',
        NOW() - INTERVAL '3 days',
        'ai-news',
        'Sarah Chen',
        'Machine Learning',
        0.91,
        0.89,
        false,
        NOW(),
        NOW()
    ),
    (
        gen_random_uuid(),
        'European Union Passes Landmark AI Regulation Act',
        'Comprehensive AI regulation framework establishes safety standards, transparency requirements, and ethical guidelines.',
        'The European Parliament has approved the AI Act, the world''s first comprehensive regulatory framework for artificial intelligence. The legislation establishes risk-based requirements for AI systems, with stricter rules for high-risk applications in healthcare, law enforcement, and critical infrastructure. Key provisions include mandatory transparency for AI-generated content, prohibitions on social scoring and real-time biometric surveillance in public spaces, and requirements for human oversight of automated decision-making. Tech companies have two years to comply with the new regulations. While industry groups warn about potential innovation constraints, consumer advocates praise the Act as necessary protection against AI risks.',
        'https://eu-parliament.example.com/ai-act',
        'https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=800',
        NOW() - INTERVAL '4 days',
        'mit-news',
        'Elena Kowalski',
        'Ethics',
        0.72,
        0.94,
        true,
        NOW(),
        NOW()
    ),
    (
        gen_random_uuid(),
        'Meta''s LLaMA 3 Open-Source Model Rivals GPT-4 in Benchmark Tests',
        'Facebook''s parent company releases powerful open-source language model, democratizing access to advanced AI.',
        'Meta has released LLaMA 3, an open-source large language model that performs comparably to GPT-4 on many benchmark tests while being freely available to researchers and developers. The 70-billion parameter model excels at reasoning, coding, and multilingual understanding. Meta''s decision to open-source LLaMA 3 aims to democratize AI development and enable innovation across academia and industry. The release includes comprehensive documentation, fine-tuning guides, and safety guardrails. Within 48 hours, developers had created dozens of applications and specialized versions. The move intensifies competition in the AI space and challenges the closed-source approach of companies like OpenAI and Anthropic.',
        'https://meta.example.com/llama3-release',
        'https://images.unsplash.com/photo-1535378917042-10a22c95931a?w=800',
        NOW() - INTERVAL '5 days',
        'tech-crunch',
        'David Kim',
        'Machine Learning',
        0.86,
        0.87,
        false,
        NOW(),
        NOW()
    )
ON CONFLICT (url) DO NOTHING;

-- Verificar la inserción
SELECT COUNT(*) as total_articles FROM articles;
SELECT COUNT(*) as total_sources FROM sources;

-- Mostrar algunos artículos
SELECT title, author, category, published_at 
FROM articles 
ORDER BY published_at DESC 
LIMIT 5;
"@

Write-Host "[INFO] Ejecutando SQL en PostgreSQL..." -ForegroundColor Yellow

# Ejecutar SQL directamente usando pipe (usuario: dev_user, db: ai_news_dev_db)
$sql | docker exec -i ai_news_postgres psql -U dev_user -d ai_news_dev_db

Write-Host ""
Write-Host "[SUCCESS] ¡Base de datos poblada exitosamente!" -ForegroundColor Green
Write-Host ""
Write-Host "Accede a la aplicación en:" -ForegroundColor Cyan
Write-Host "  Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "  Backend API: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Para verificar los datos:" -ForegroundColor Yellow
Write-Host "  docker exec ai_news_postgres psql -U dev_user -d ai_news_dev_db -c 'SELECT COUNT(*) FROM articles;'" -ForegroundColor Gray
Write-Host ""
