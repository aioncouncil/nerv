// Debug patch for NERV - Add this to the console if needed
console.log('🔧 NERV Debug Patch Loading...');

// Test if NERV app loaded
if (window.nerv) {
    console.log('✅ NERV App found:', window.nerv);
    
    // Test API connection
    if (window.nerv.apiBaseUrl) {
        console.log('🌐 API URL:', window.nerv.apiBaseUrl);
        
        fetch(window.nerv.apiBaseUrl.replace('/api/v1', '') + '/health')
            .then(r => r.json())
            .then(data => console.log('✅ API Health:', data))
            .catch(e => console.log('❌ API Error:', e));
    }
    
    // Test canvas
    if (window.nerv.stage) {
        console.log('🎨 Canvas found:', window.nerv.stage);
    } else {
        console.log('❌ Canvas not initialized');
    }
    
    // Test tool selection
    console.log('🔧 Testing tool selection...');
    setTimeout(() => {
        const pointBtn = document.querySelector('[data-tool="point"]');
        if (pointBtn) {
            console.log('✅ Point tool button found');
            pointBtn.click();
            console.log('✅ Point tool clicked');
        } else {
            console.log('❌ Point tool button not found');
        }
    }, 1000);
    
} else {
    console.log('❌ NERV App not found - checking initialization...');
    
    // Check if DOM loaded
    if (document.readyState === 'loading') {
        console.log('⏳ DOM still loading...');
    } else {
        console.log('✅ DOM ready, but NERV not initialized');
        
        // Check if Konva loaded
        if (typeof Konva !== 'undefined') {
            console.log('✅ Konva loaded');
        } else {
            console.log('❌ Konva not loaded');
        }
    }
}