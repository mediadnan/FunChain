const mermaidChangeTheme = theme => {
    if (theme === 'auto')
        theme = window.matchMedia("(prefers-color-scheme: dark)").matches ? 'dark' : 'light';
    const op = theme === 'light' ? e => {
        if (!e.classList.contains("light"))
            e.classList.add('light');
        e.classList.remove('dark');
    } : e => {
        e.classList.remove('light')
        if (!e.classList.contains("dark"))
            e.classList.add("dark");
    };
    document.querySelectorAll('.mermaid').forEach(op);
    console.log(`Mermaid Theme: Changed theme to ${theme}`)
}

const LIGHT_COLOR = '#e5e9eb';
const DARK_COLOR = '#333333'

const toggleTheme = () => {
    theme = document.body.dataset.theme;
    if (theme !== "light" && theme != "dark")
        theme = window.matchMedia("(prefers-color-scheme: dark)").matches ? 'dark' : 'light';
    const primary = theme === 'light' ? DARK_COLOR : LIGHT_COLOR;
    const onPrimary = theme === 'light' ? LIGHT_COLOR : DARK_COLOR;

    document.querySelectorAll('.mermaid').forEach(e => {
        e.querySelectorAll('.edgePaths path').forEach(x => {
            x.style.stroke = primary;
            // x.style.fill = primary;
        })
        e.querySelector('.flowchart-pointEnd').style.stroke = primary;
        e.querySelectorAll(".node ").forEach(e => {
            x.style.stroke = primary;
            x.style.fill = onPrimary;
        })
    })
}

(() => {
    document.addEventListener("DOMContentLoaded", () => {
        const theme = document.body.dataset.theme;
        // theme && mermaidChangeTheme(theme);
        theme && toggleTheme(theme);
        document.querySelector('button.theme-toggle').addEventListener('click', toggleTheme);
    })
})();