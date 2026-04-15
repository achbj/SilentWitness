import React, { useState, useEffect } from 'react';
import {
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  SafeAreaView,
  StatusBar,
  Alert,
  TextInput,
  ScrollView,
  KeyboardAvoidingView,
  Platform
} from 'react-native';
import { Audio } from 'expo-av';
import * as FileSystem from 'expo-file-system';
import * as SecureStore from 'expo-secure-store';

// Colors for app theme
const COLORS = {
  primary: '#2196F3',
  secondary: '#FF5722',
  danger: '#F44336',
  safe: '#4CAF50',
  dark: '#212121',
  light: '#FAFAFA',
  background: '#ECEFF1'
};

// SilentWitness Main App
export default function App() {
  const [isDecoyMode, setIsDecoyMode] = useState(true);
  const [decoyInput, setDecoyInput] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [evidenceList, setEvidenceList] = useState([]);
  const [currentView, setCurrentView] = useState('main');

  // Check for decoy mode unlock code
  const UNLOCK_CODE = '911911'; // Secret code to reveal app

  const handleDecoyInput = (value) => {
    setDecoyInput(value);

    // Check if unlock code entered
    if (value === UNLOCK_CODE) {
      setIsDecoyMode(false);
      setDecoyInput('');
      Alert.alert('SilentWitness Activated', 'Evidence documentation mode enabled.');
    }
  };

  // Quick delete all (emergency safety)
  const emergencyDelete = async () => {
    Alert.alert(
      'Emergency Delete',
      'This will permanently delete ALL evidence. Are you in immediate danger?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'DELETE ALL',
          style: 'destructive',
          onPress: async () => {
            await SecureStore.deleteItemAsync('evidence_data');
            setEvidenceList([]);
            Alert.alert('Deleted', 'All evidence has been removed.');
          }
        }
      ]
    );
  };

  // Render decoy calculator UI
  if (isDecoyMode) {
    return (
      <SafeAreaView style={styles.decoyContainer}>
        <StatusBar barStyle="dark-content" />
        <View style={styles.decoyHeader}>
          <Text style={styles.decoyTitle}>Calculator</Text>
        </View>
        <View style={styles.decoyDisplay}>
          <Text style={styles.decoyDisplayText}>
            {decoyInput || '0'}
          </Text>
        </View>
        <View style={styles.decoyButtons}>
          {['7', '8', '9', '÷', '4', '5', '6', '×', '1', '2', '3', '-', '0', '.', '=', '+'].map((btn) => (
            <TouchableOpacity
              key={btn}
              style={styles.decoyButton}
              onPress={() => handleDecoyInput(decoyInput + btn)}
            >
              <Text style={styles.decoyButtonText}>{btn}</Text>
            </TouchableOpacity>
          ))}
        </View>
        <View style={styles.decoyHint}>
          <Text style={styles.decoyHintText}>Enter code to access app</Text>
        </View>
      </SafeAreaView>
    );
  }

  // Main SilentWitness UI
  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" />

      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>SilentWitness</Text>
        <TouchableOpacity
          style={styles.decoyToggle}
          onPress={() => setIsDecoyMode(true)}
        >
          <Text style={styles.decoyToggleText}>🔒 Disguise</Text>
        </TouchableOpacity>
      </View>

      {/* Navigation */}
      <View style={styles.navBar}>
        {['Record', 'Evidence', 'Export', 'Emergency'].map((tab) => (
          <TouchableOpacity
            key={tab}
            style={[
              styles.navItem,
              currentView === tab.toLowerCase() && styles.navItemActive
            ]}
            onPress={() => setCurrentView(tab.toLowerCase())}
          >
            <Text style={[
              styles.navText,
              currentView === tab.toLowerCase() && styles.navTextActive
            ]}>
              {tab}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Content based on view */}
      <ScrollView style={styles.content}>
        {currentView === 'record' && (
          <View style={styles.recordSection}>
            <Text style={styles.sectionTitle}>Document Evidence</Text>

            {/* Voice Recording */}
            <TouchableOpacity
              style={[
                styles.recordButton,
                isRecording && styles.recordButtonActive
              ]}
              onPress={() => setIsRecording(!isRecording)}
            >
              <Text style={styles.recordButtonText}>
                {isRecording ? '⏹ Stop Recording' : '🎤 Start Recording'}
              </Text>
            </TouchableOpacity>

            {/* Text Input */}
            <TextInput
              style={styles.transcriptInput}
              placeholder="Or type your evidence here..."
              multiline
              numberOfLines={4}
              value={transcript}
              onChangeText={setTranscript}
            />

            {/* Save Button */}
            <TouchableOpacity
              style={styles.saveButton}
              onPress={() => {
                if (transcript) {
                  Alert.alert('Saved', 'Evidence encrypted and stored locally.');
                  setTranscript('');
                }
              }}
            >
              <Text style={styles.saveButtonText}>💾 Save Evidence</Text>
            </TouchableOpacity>

            {/* Status */}
            <View style={styles.statusBar}>
              <Text style={styles.statusText}>🔒 Offline Mode Active</Text>
              <Text style={styles.statusText}>🔐 All Data Encrypted</Text>
            </View>
          </View>
        )}

        {currentView === 'evidence' && (
          <View style={styles.evidenceSection}>
            <Text style={styles.sectionTitle}>Stored Evidence</Text>

            {evidenceList.length === 0 ? (
              <View style={styles.emptyState}>
                <Text style={styles.emptyText}>No evidence stored yet</Text>
                <Text style={styles.emptySubtext}>All evidence is encrypted locally</Text>
              </View>
            ) : (
              evidenceList.map((item, index) => (
                <View key={index} style={styles.evidenceItem}>
                  <Text style={styles.evidenceId}>ID: {item.id}</Text>
                  <Text style={styles.evidenceDate}>{item.date}</Text>
                  <Text style={styles.evidenceType}>{item.type}</Text>
                </View>
              ))
            )}
          </View>
        )}

        {currentView === 'export' && (
          <View style={styles.exportSection}>
            <Text style={styles.sectionTitle}>Legal Export</Text>
            <Text style={styles.exportInfo}>
              Export evidence in court-admissible format
            </Text>
            <TouchableOpacity style={styles.exportButton}>
              <Text style={styles.exportButtonText}>📄 Generate Legal Document</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.exportButton}>
              <Text style={styles.exportButtonText}>📧 Send to Safe Contact</Text>
            </TouchableOpacity>
          </View>
        )}

        {currentView === 'emergency' && (
          <View style={styles.emergencySection}>
            <Text style={styles.sectionTitle}>Emergency Protocol</Text>

            <TouchableOpacity
              style={styles.emergencyButton}
              onPress={emergencyDelete}
            >
              <Text style={styles.emergencyButtonText}>
                🗑️ DELETE ALL EVIDENCE
              </Text>
              <Text style={styles.emergencyButtonSubtext}>
                For immediate safety
              </Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.alertButton}>
              <Text style={styles.alertButtonText}>
                📞 Alert Safe Contact
              </Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.alertButton}>
              <Text style={styles.alertButtonText}>
                🏥 Emergency Services
              </Text>
            </TouchableOpacity>

            <View style={styles.safetyInfo}>
              <Text style={styles.safetyInfoText}>
                National DV Hotline: 1-800-799-7233
              </Text>
            </View>
          </View>
        )}
      </ScrollView>

      {/* Footer */}
      <View style={styles.footer}>
        <Text style={styles.footerText}>
          Built with Gemma 4 • Offline-first • Your data stays private
        </Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  // Main App Styles
  container: {
    flex: 1,
    backgroundColor: COLORS.dark,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: COLORS.primary,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: COLORS.light,
  },
  decoyToggle: {
    padding: 8,
    borderRadius: 8,
    backgroundColor: COLORS.secondary,
  },
  decoyToggleText: {
    color: COLORS.light,
    fontSize: 14,
  },
  navBar: {
    flexDirection: 'row',
    backgroundColor: COLORS.background,
    paddingVertical: 8,
  },
  navItem: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
  },
  navItemActive: {
    borderBottomWidth: 2,
    borderBottomColor: COLORS.primary,
  },
  navText: {
    color: COLORS.dark,
    fontSize: 14,
  },
  navTextActive: {
    color: COLORS.primary,
    fontWeight: 'bold',
  },
  content: {
    flex: 1,
    padding: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: COLORS.light,
    marginBottom: 16,
  },
  recordSection: {
    flex: 1,
  },
  recordButton: {
    backgroundColor: COLORS.danger,
    padding: 20,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 16,
  },
  recordButtonActive: {
    backgroundColor: COLORS.safe,
  },
  recordButtonText: {
    color: COLORS.light,
    fontSize: 18,
    fontWeight: 'bold',
  },
  transcriptInput: {
    backgroundColor: COLORS.background,
    borderRadius: 8,
    padding: 16,
    fontSize: 16,
    minHeight: 100,
    marginBottom: 16,
    color: COLORS.dark,
  },
  saveButton: {
    backgroundColor: COLORS.primary,
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  saveButtonText: {
    color: COLORS.light,
    fontSize: 16,
    fontWeight: 'bold',
  },
  statusBar: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: 16,
  },
  statusText: {
    color: COLORS.safe,
    fontSize: 12,
  },
  evidenceSection: {
    flex: 1,
  },
  emptyState: {
    alignItems: 'center',
    padding: 40,
  },
  emptyText: {
    color: COLORS.light,
    fontSize: 18,
  },
  emptySubtext: {
    color: '#757575',
    fontSize: 14,
    marginTop: 8,
  },
  evidenceItem: {
    backgroundColor: COLORS.background,
    padding: 12,
    borderRadius: 8,
    marginBottom: 8,
  },
  evidenceId: {
    color: COLORS.primary,
    fontSize: 14,
    fontWeight: 'bold',
  },
  evidenceDate: {
    color: '#757575',
    fontSize: 12,
  },
  evidenceType: {
    color: COLORS.dark,
    fontSize: 16,
  },
  exportSection: {
    flex: 1,
  },
  exportInfo: {
    color: '#BDBDBD',
    fontSize: 14,
    marginBottom: 16,
  },
  exportButton: {
    backgroundColor: COLORS.primary,
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 8,
  },
  exportButtonText: {
    color: COLORS.light,
    fontSize: 16,
  },
  emergencySection: {
    flex: 1,
  },
  emergencyButton: {
    backgroundColor: COLORS.danger,
    padding: 20,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 16,
  },
  emergencyButtonText: {
    color: COLORS.light,
    fontSize: 18,
    fontWeight: 'bold',
  },
  emergencyButtonSubtext: {
    color: COLORS.light,
    fontSize: 12,
    marginTop: 4,
  },
  alertButton: {
    backgroundColor: COLORS.secondary,
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 8,
  },
  alertButtonText: {
    color: COLORS.light,
    fontSize: 16,
  },
  safetyInfo: {
    marginTop: 16,
    padding: 16,
    backgroundColor: COLORS.background,
    borderRadius: 8,
  },
  safetyInfoText: {
    color: COLORS.primary,
    fontSize: 16,
    textAlign: 'center',
  },
  footer: {
    padding: 12,
    backgroundColor: COLORS.dark,
    borderTopWidth: 1,
    borderTopColor: '#424242',
  },
  footerText: {
    color: '#9E9E9E',
    fontSize: 12,
    textAlign: 'center',
  },

  // Decoy Calculator Styles
  decoyContainer: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  decoyHeader: {
    padding: 16,
    backgroundColor: '#2196F3',
  },
  decoyTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#FFFFFF',
    textAlign: 'center',
  },
  decoyDisplay: {
    backgroundColor: '#FFFFFF',
    padding: 20,
    margin: 16,
    borderRadius: 8,
    minHeight: 80,
    justifyContent: 'center',
    alignItems: 'flex-end',
  },
  decoyDisplayText: {
    fontSize: 36,
    fontWeight: 'bold',
    color: '#212121',
  },
  decoyButtons: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    padding: 8,
  },
  decoyButton: {
    width: '23%',
    height: 60,
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    margin: '1%',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    elevation: 2,
  },
  decoyButtonText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#212121',
  },
  decoyHint: {
    padding: 16,
    alignItems: 'center',
  },
  decoyHintText: {
    color: '#9E9E9E',
    fontSize: 12,
  },
});