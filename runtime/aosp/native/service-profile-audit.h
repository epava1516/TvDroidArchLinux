#pragma once
// Observe original parser acceptance without another RC grammar or handler execution.
// The caller must reject the whole parse on any error. Tokens are declarations,
// not resolved runtime effects, permission decisions or service readiness.
#include "parser.h"
#include <memory>
#include <string>
#include <vector>
namespace archtv::aosp {
struct ProfileLine {
    int line;
    std::vector<std::string> tokens;
};
struct ProfileSection {
    std::string kind, filename;
    int line;
    std::vector<std::string> header;
    std::vector<ProfileLine> lines;
};
class AuditedSectionParser final : public android::init::SectionParser {
 public:
    AuditedSectionParser(std::string kind,
                         std::unique_ptr<android::init::SectionParser> original,
                         std::vector<ProfileSection>& output)
        : kind_(std::move(kind)), original_(std::move(original)), output_(output) {}
    android::base::Result<void> ParseSection(std::vector<std::string>&& args,
                                             const std::string& filename, int line) override {
        current_={kind_,filename,line,args};
        auto result=original_->ParseSection(std::move(args),filename,line);
        active_=result.ok();
        return result;
    }
    android::base::Result<void> ParseLineSection(std::vector<std::string>&& args,int line) override {
        auto copy=args;
        auto result=original_->ParseLineSection(std::move(args),line);
        if (active_ && result.ok()) current_.lines.push_back({line,std::move(copy)});
        return result;
    }
    android::base::Result<void> EndSection() override {
        auto result=original_->EndSection();
        if (active_ && result.ok()) output_.push_back(std::move(current_));
        active_=false;
        return result;
    }
    void EndFile() override { original_->EndFile(); }
 private:
    std::string kind_;
    std::unique_ptr<android::init::SectionParser> original_;
    std::vector<ProfileSection>& output_;
    ProfileSection current_{};
    bool active_=false;
};
}
