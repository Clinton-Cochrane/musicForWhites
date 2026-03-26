import "package:flutter/material.dart";

void main() {
  runApp(const MusicWordFilterApp());
}

class MusicWordFilterApp extends StatelessWidget {
  const MusicWordFilterApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: "Music Word Filter",
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.indigo),
        useMaterial3: true,
      ),
      home: const FilterSettingsScreen(),
    );
  }
}

class FilterSettingsScreen extends StatefulWidget {
  const FilterSettingsScreen({super.key});

  @override
  State<FilterSettingsScreen> createState() => _FilterSettingsScreenState();
}

class _FilterSettingsScreenState extends State<FilterSettingsScreen> {
  bool censorEnabled = true;
  final TextEditingController blocklistController =
      TextEditingController(text: "nigg");
  final TextEditingController allowlistController = TextEditingController();
  final TextEditingController testWordController = TextEditingController();

  @override
  void dispose() {
    blocklistController.dispose();
    allowlistController.dispose();
    testWordController.dispose();
    super.dispose();
  }

  List<String> _parseTerms(String raw) {
    return raw
        .split(",")
        .map((value) => value.trim().toLowerCase())
        .where((value) => value.isNotEmpty)
        .toList();
  }

  bool _shouldMuteWord(String word) {
    if (!censorEnabled) {
      return false;
    }

    final normalizedWord = word.trim().toLowerCase();
    if (normalizedWord.isEmpty) {
      return false;
    }

    final blocklist = _parseTerms(blocklistController.text);
    final allowlist = _parseTerms(allowlistController.text);

    final isAllowed = allowlist.any((term) => normalizedWord.contains(term));
    if (isAllowed) {
      return false;
    }

    return blocklist.any((term) => normalizedWord.contains(term));
  }

  @override
  Widget build(BuildContext context) {
    final shouldMutePreview = _shouldMuteWord(testWordController.text);

    return Scaffold(
      appBar: AppBar(
        title: const Text("Music Word Filter"),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            SwitchListTile(
              title: Text(censorEnabled ? "Censor N-word" : "Allow N-word"),
              subtitle: const Text("Main behavior toggle"),
              value: censorEnabled,
              onChanged: (value) {
                setState(() {
                  censorEnabled = value;
                });
              },
            ),
            const SizedBox(height: 12),
            TextField(
              controller: blocklistController,
              decoration: const InputDecoration(
                labelText: "Blocklist terms (comma separated)",
                border: OutlineInputBorder(),
              ),
              onChanged: (_) => setState(() {}),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: allowlistController,
              decoration: const InputDecoration(
                labelText: "Allowlist terms (comma separated)",
                border: OutlineInputBorder(),
              ),
              onChanged: (_) => setState(() {}),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: testWordController,
              decoration: const InputDecoration(
                labelText: "Type a word to test the rule",
                border: OutlineInputBorder(),
              ),
              onChanged: (_) => setState(() {}),
            ),
            const SizedBox(height: 12),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Text(
                  shouldMutePreview
                      ? "Result: this word WOULD be muted."
                      : "Result: this word would NOT be muted.",
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}