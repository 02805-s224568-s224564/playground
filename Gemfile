source "https://rubygems.org"

# The site is built by GitHub Actions (see .github/workflows/pages.yml), not by
# the legacy Pages branch build, so we are free to use any gem we like here.
gem "jekyll", "~> 4.4"

# webrick left Ruby's stdlib in 3.0; `jekyll serve` needs it explicitly.
gem "webrick", "~> 1.9"

group :jekyll_plugins do
  gem "jekyll-feed", "~> 0.17"    # /feed.xml
  gem "jekyll-seo-tag", "~> 2.8"  # <title>, OpenGraph, description meta
  gem "jekyll-sitemap", "~> 1.4"  # /sitemap.xml
end
